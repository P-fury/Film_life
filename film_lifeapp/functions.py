import os


import pytz
# ========= PDF DOCU ====================
from django.http import FileResponse
import io
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from timezonefinder import TimezoneFinder

from FILM_WORK_CALC import settings
# ========= PDF -> iCalendar ====================
import locale
from pdfminer.high_level import extract_text
import pytesseract
from pdf2image import convert_from_path, exceptions
from ics import Calendar, Event
import io
import re
import tempfile
from datetime import datetime



def create_pdf(project):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    font_path = os.path.join(settings.BASE_DIR, 'film_lifeapp/static/fonts/bitter/Bitter-Regular.ttf')
    pdfmetrics.registerFont(TTFont('Bitter', font_path))
    font_path2 = os.path.join(settings.BASE_DIR, 'film_lifeapp/static/fonts/bitter/Bitter-Bold.ttf')
    pdfmetrics.registerFont(TTFont('Bitter-Bold', font_path2))

    def draw_table(tab_data, start_y):
        table_start_y = start_y
        cell_width = 100
        cell_height = 20
        row_height = 20
        c.setStrokeColorRGB(0, 0, 0)  # Set line color to black

        # Draw data rows
        for j, header_text in enumerate(tab_data[0]):
            x = 50 + j * cell_width
            y = table_start_y
            if table_start_y == 750:  # Check if it's not the first row of the page
                c.rect(x, y, cell_width, cell_height)  # Draw white background for non-header cells
                c.setFillGray(0)  # Set text color to black
                column_font_size = 10
                c.setFont('Bitter', column_font_size)  # Set font and size for header text
                text_width = c.stringWidth(header_text, 'Bitter', column_font_size)
                c.drawString(x + (cell_width - text_width) / 2, y + 5, header_text)  # Draw header text
            else:
                header_font_size = 12  # Set the font size for the header text
                c.setFont('Bitter', header_font_size)  # Set font and size for header text
                c.setFillColorRGB(0.8, 0.8, 0.8)  # Gray fill color for header cells
                c.rect(x, y, cell_width, cell_height, fill=True)  # Draw gray background for header cells
                c.setFillGray(0)  # Set text color to black
                # Adjust x coordinate to center text horizontally
                text_width = c.stringWidth(header_text, 'Bitter-Bold', header_font_size)
                c.drawString(x + (cell_width - text_width) / 2, y + 5, header_text)  # Draw header text

        # watermark
        c.setFont('Bitter', 5)
        c.setFillColor(colors.grey)
        c.drawString(520, 10, "created by film_lifeapp")

        # Draw data rows
        c.setFont('Bitter', 10)  # Set font and size for data cells
        for i, row in enumerate(tab_data[1:], start=1):
            if (table_start_y - i * row_height) < 80:
                c.showPage()  # If remaining space on the page is less than one row height, start a new page
                table_start_y = 750  # Reset the starting position for the table
                draw_table(tab_data[i:], table_start_y)  # Recursively draw the remaining rows on the new page
                break
            for j, cell in enumerate(row):
                x = 50 + j * cell_width
                y = table_start_y - i * row_height
                c.rect(x, y, cell_width, cell_height)  # Draw cell border
                c.setFillGray(0)  # Set text color to black
                # Adjust x coordinate to center text horizontally
                text_width = c.stringWidth(cell, 'Bitter', 10)
                c.drawString(x + (cell_width - (text_width)) / 2, y + 5, cell)

        total_earnings = project.total_earnings_for_project
        total_overhours = sum([int(x.amount_of_overhours) for x in project.workday_set.all()])
        c.setFont('Bitter', 12)
        c.drawString(30, 70, f"Total overhours: {total_overhours}")
        c.drawString(450, 70, f"Total earned: {total_earnings},-")

    # Adding title
    c.setFont('Bitter', 16)
    c.drawString(40, 750, F"{project.name}:")
    c.drawString(40, 730, F"Occupation: {project.occupation}")
    c.drawString(40, 710, F"Daily rate: {project.daily_rate}")
    c.drawString(40, 690, F"Overhours: {project.type_of_overhours}%")

    # Data for the table
    tab_data = [
        ['NO:', 'DATE:', 'OVERHOURS:', 'TYPE OF DAY:', 'EARNED:'],
    ]
    # Filling data from the project's workdays
    for index, day in enumerate(project.workday_set.all().order_by('date')):
        tab_data.append(
            [str(index + 1), str(day.date), str(day.amount_of_overhours), day.type_of_workday, str(day.earnings)])
    # Draw the table
    draw_table(tab_data, 640)

    # Save the PDF canvas
    c.save()
    pdf_buffer.seek(0)

    return pdf_buffer


# TIMEZONE CHECKER =====
def find_timezone(city):
    lat = city.latitude
    long = city.longitude
    tf = TimezoneFinder()
    timezone = tf.timezone_at(lat=lat, lng=long)
    if timezone:
        selected_timezone = pytz.timezone(f'{timezone}')
        return selected_timezone
    else:
        selected_timezone = pytz.timezone('UTC')
        return selected_timezone


#================== CONVERT PDF TO ICALENDAR ============
daysearchpl = re.compile(
    r'(?:(?:KONIEC DNIA|End Day|Koniec dnia zdjęciowego|END OF DAY|PODSUMOWANIE DNIA|End of Shooting Day)'
    r'[^0-9]*?(?:nr|#|NR)?\s?(\d+)[^0-9]*?'
    r'(\b(?:poniedziałek|wtorek|środa|czwartek|piątek|sobota|niedziela)\b)[^0-9]*'
    r'(\d{1,2} \w+ \d{4}))|'
    r'(\b(?:poniedziałek|wtorek|środa|czwartek|piątek|sobota|niedziela)\b, (\d{1,2} \w+ \d{4})) --- '
    r'PODSUMOWANIE DNIA (?:nr|#|NR)?\s?(\d+) ---',
    re.IGNORECASE
)


def convert_date(date_str):
    return datetime.strptime(date_str, '%d %B %Y')


def extract_text_from_images(file_path):
    try:
        images = convert_from_path(file_path, dpi=300)
    except exceptions.PDFPageCountError as e:
        raise Exception(f"Failed to convert PDF to images: {e}")

    text = ""
    for image in images:
        text += pytesseract.image_to_string(image, lang='pol')
    return text


def process_pdf(file, project_name):
    locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
    pdf_content = None
    try:
        file.seek(0)
        pdf_content = file.read()
        if not pdf_content:
            raise Exception("PDF file is empty or could not be read.")

        pdf_text = extract_text(io.BytesIO(pdf_content))
    except Exception as e:
        print(f"Failed to extract text from PDF: {e}")
        pdf_text = ""

    matches = list(daysearchpl.finditer(pdf_text))
    if not matches and pdf_content:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            temp_pdf.write(pdf_content)
            temp_pdf_path = temp_pdf.name
        try:
            pdf_text = extract_text_from_images(temp_pdf_path)
            matches = list(daysearchpl.finditer(pdf_text))
        except Exception as e:
            print(f"Failed to convert PDF to images or extract text from images: {e}")
            raise Exception(f"Cannot read PDF file: {e}")
        finally:
            os.remove(temp_pdf_path)

    events = []
    for match in matches:
        if match.group(1) and match.group(2) and match.group(3):
            day_number = match.group(1)
            day_of_week = match.group(2)
            date_str = match.group(3)
        elif match.group(5) and match.group(6):
            day_of_week = match.group(4)
            date_str = match.group(5)
            day_number = match.group(6)
        else:
            continue

        date = convert_date(date_str)
        event_name = f"{project_name} dzien: {day_number}"
        event = {
            "date": date,
            "description": event_name,
            "location": ""
        }
        events.append(event)

    cal = Calendar()
    for event in events:
        cal_event = Event()
        cal_event.name = event['description']
        cal_event.begin = event['date'].replace(tzinfo=None)
        cal_event.end = event['date'].replace(tzinfo=None)
        cal_event.description = event['description']
        cal_event.location = event['location']
        cal.events.add(cal_event)
    return cal