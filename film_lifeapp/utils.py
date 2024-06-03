import matplotlib.pyplot as plt
import base64
from io import BytesIO


def get_graph():
    buffer = BytesIO()
    plt.savefig(buffer, format='png', transparent=True)
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png).decode('utf-8')
    buffer.close()
    return graph


# def get_barplot(x, y):
#     plt.switch_backend('agg')
#     plt.figure(figsize=(8, 4))
#     plt.title("Projects")
#     plt.xlabel("Projects Names", fontsize=10)
#     plt.xticks(fontsize=6)
#     plt.ylabel("Earned")
#     plt.yticks(fontsize=8, rotation=-30)
#     plt.tight_layout()
#     plt.bar(x, y)
#     graph = get_graph()
#     return graph


def get_piechart(x, y):
    plt.switch_backend('agg')
    explode = [0.1 if i == 0 else 0 for i in range(len(x))]
    plt.figure(figsize=(7, 7))
    plt.title("Earning wheel", fontsize=12)
    colors = plt.cm.Set3.colors
    plt.pie(x, explode=explode, autopct='%1.1f%%', shadow=True, colors=colors, pctdistance=1.1)
    plt.rcParams['font.size'] = 8
    legend = plt.legend(y, loc='upper right', bbox_to_anchor=(1.2, 1))
    frame = legend.get_frame()
    frame.set_facecolor((0.74, 0.83, 0.9, 1))
    plt.tight_layout()
    graph = get_graph()
    return graph
