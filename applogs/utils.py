import io
import xlwt
from contextlib import contextmanager


class XLSWriterUtil:
    """
    Сборник полезностей для экспорта отчётов.

    В том числе хранит дефолтную позицию и стиль, т.е. немного упрощает запись:
        with self.add_position(row_num, col_num):
            self.write(0, 0, 'val0')
            self.write(0, 1, 'val1')
    вместо:
        self.ws.write(row_num, col_num,     'val0')
        self.ws.write(row_num, col_num + 1, 'val1')

    Аналогично со стилями:
        with self.add_style({'align': 'horizontal center'}):
            self.write(0, 0, 'val0')
            self.write(0, 1, 'val1', {'font': 'bold on'})
    вместо:
        self.ws.write(0, 0, 'val0', {'align': 'horizontal center'})
        self.ws.write(0, 1, 'val1', {'align': 'horizontal center', 'font': 'bold on'})
    """
    def __init__(self):
        self.wb = None  # Workbook
        self.ws = None  # Worksheet
        self.r = 0  # текущая строка
        self.c = 0  # текущий столбец
        self.style = {}  # текущий стиль
        # запоминает последний сгенерированный из dict'а стиль;
        # если при следующей генерации словарь не изменился, используется закешированный стиль отсюда
        self._last_used_style = (None, None)

    def write(self, r, c, label='', style={}):
        """ Записыват `label` в ячейку в колонке `r` и столбце `c` относительно текущего расположения. """
        xfstyle = self.dict_style_to_xf(self.merge_styles(self.style, style))
        self.ws.write(self.r+r, self.c+c, label, xfstyle)

    def write_merge(self, r, r1, c, c1, label='', style={}):
        """ Записыват `label` в ячейку в колонке `r` и столбце `c` относительно текущего расположения,
            объединяет ячейки до `r1:c1` включительно. """
        xfstyle = self.dict_style_to_xf(self.merge_styles(self.style, style))
        self.ws.write_merge(self.r+r, self.r+r1, self.c+c, self.c+c1, label, xfstyle)

    def col(self, c):
        """ Возвращает столбец с индексом `c` относительно текущего """
        return self.ws.col(self.c+c)

    def row(self, r):
        """ Возвращает строку с индексом `r` относительно текущей """
        return self.ws.row(self.r+r)

    def get_width_for_col(self, num_characters):
        """ Возвращет ширину колонки для записи в `width`. Точность сомнительна, но вроде работает. """
        return (num_characters + 3) * 230

    def dict_style_to_xf(self, style):
        """ Конвертирует словарь с параметрами стиля в `XFStyle` """
        if self._last_used_style[0] == style:
            return self._last_used_style[1]
        kwags = {}
        if 'num_format_str' in style:
            kwags['num_format_str'] = style.pop('num_format_str')
        xfstyle = xlwt.easyxf("; ".join(f'{k}: {v}' for k, v in style.items()), **kwags)
        self._last_used_style = (style, xfstyle)
        return xfstyle

    def merge_styles(self, style0, style1):
        """ Объединяет два стиля-словаря (накладывает style1 на style0) """
        res = style0.copy()
        res.update(style1)
        return res

    @contextmanager
    def add_style(self, new_style):
        """ Применяет `new_style` поверх текущего, выполняет блок с ним, возвращает старый обратно """
        old_style = self.style
        self.style = self.merge_styles(self.style, new_style)
        yield
        self.style = old_style

    @contextmanager
    def add_position(self, dr, dc):
        """ Сдвигает текущую строку и столбец на `dr` и `dc`, выполнет блок с ними, возвращает старые значения """
        old_pos = (self.r, self.c)
        self.r, self.c = self.r+dr, self.c+dc
        yield
        self.r, self.c = old_pos

    def generate(self):
        """ Основной местод генерации, должен создать xlwt.Workbook и положить его в self.wb """
        raise NotImplementedError('subclasses of XLSWriterUtil must provide generate() method')

    def generate_as_buffer(self):
        """ Генерит и сохраняет Workbook в файлоподобный буфер, возвращает последний """
        f = io.BytesIO()
        self.generate()
        self.wb.save(f)
        f.seek(0)
        return f
