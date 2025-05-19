import pandas as pd
import pymongo
import datetime
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, HBar, LabelSet, Slider, DatePicker, CustomJS
from bokeh.plotting import figure

# 连接 MongoDB
client = pymongo.MongoClient("mongodb://root:Zqx167613@192.168.2.3:27017")
db = client['微博']
dates = sorted(db.list_collection_names())

def get_data(k):
    global data_, timelist
    col = db[k]
    one = col.find({}, {"_id": 0})
    arry = list(one)
    headers = ['排名', '标签', '话题', '热度', '时间']
    df = pd.DataFrame(arry).set_index('时间')
    data_ = df.groupby(by='时间')
    timelist = list(keys for keys, values in data_)
    return data_, timelist

def get_daf(i):
    dict_i = data_.get_group(timelist[i]).copy()
    dict_i["位置"] = dict_i['热度'] / 2
    dict_i['热度1'] = "raw_hot=" + dict_i['热度'].astype('str')
    daf = dict_i[dict_i['排名'] <= 50]
    daf['真排名'] = dict_i['排名'].astype('str')
    daf['排名'] = dict_i['排名'][::-1] 
    max_ = daf["热度"].max()
    timemes = timelist[i]
    return daf, max_, timemes

# 默认加载今天的数据
today = datetime.date.today()
today = str(today)
data_box = get_data(today)
data_ = data_box[0]
timelist = data_box[1]
box = get_daf(0)
daf = box[0]
max_ = box[1]
timemes = box[2]
longsize = 4000000

source = ColumnDataSource(data=daf)
p = figure(
    y_range=(0, 50.5),
    x_range=(-0.02 * longsize, longsize),
    title=None,
    sizing_mode="stretch_width",
    height_policy='fixed',
    height=2000,
    x_axis_location='above',
    tools=['tap', 'reset'],
    toolbar_location=None
)

glyph1 = HBar(y='排名', right=longsize, height=0.8, fill_color='skyblue', line_color=None)
glyph2 = HBar(y='排名', right="热度", height=0.8, fill_color='red', fill_alpha=0.5, line_color=None)
labels1 = LabelSet(x=longsize / 2, y='排名', text="话题", source=source, text_align='center', y_offset=-10)
labels2 = LabelSet(x=longsize, y='排名', text="热度1", source=source, text_align='right', y_offset=-10, x_offset=-2)
labels3 = LabelSet(x=0, y='排名', text="真排名", source=source, text_align='center', y_offset=-10, x_offset=-10)

# JavaScript 回调（跳转到微博搜索页面）
callback = CustomJS(args=dict(p=p, source=source), code="""
    var selected_index = source.selected.indices[0];
    var value = source.data['话题'][selected_index];
    if (typeof(value) != "undefined") {
        window.open("https://s.weibo.com/weibo?q=%23" + value + "%23");
    }
    p.reset.emit();
""")
p.js_on_event('tap', callback)

# 滑块回调更新数据
def slider_update(attrname, old, new):
    i = slider.value
    box = get_daf(i)
    daf = box[0]
    max_ = box[1]
    timemes = box[2]
    source.data = daf
    slider.title = f'时间 {timemes}'

slider = Slider(start=0, end=len(timelist) - 1, value=1, step=1, title=f'时间 {timemes}', width_policy="max", show_value=False)
slider.on_change('value', slider_update)

# 日期选择器回调更新数据
def select_update(attrname, old, new):
    k = picker.value
    data_box = get_data(k)
    global data_, timelist
    data_ = data_box[0]
    timelist = data_box[1]
    box = get_daf(0)
    daf = box[0]
    slider.end = len(timelist) - 1
    source.data = daf

start_date = min(dates)
end_date = max(dates)
picker = DatePicker(title="日期", value=end_date, min_date=start_date, max_date=end_date, width=300)
picker.on_change('value', select_update)

p.grid.grid_line_color = None
p.axis.ticker = []
p.outline_line_color = None
p.grid.grid_line_color = None
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None

p.add_glyph(source, glyph1)
p.add_glyph(source, glyph2)
p.add_layout(labels1)
p.add_layout(labels2)
p.add_layout(labels3)

sliders = row(slider, picker)
sliders.sizing_mode = "stretch_width"
layout = column(sliders, p)
layout.sizing_mode = "stretch_both"

curdoc().add_root(layout)
curdoc().title = "微博热搜分析"