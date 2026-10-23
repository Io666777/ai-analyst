// ECharts только из нужных частей - не вся библиотека: в несколько раз меньше кода.
// Файл загружается лениво (import() в VChart): на страницах без графиков его нет вовсе
import { BarChart, LineChart } from 'echarts/charts';
import {
  AriaComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  ToolboxComponent,
  TooltipComponent,
} from 'echarts/components';
import * as echarts from 'echarts/core';
import langRU from 'echarts/lib/i18n/langRU.js';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  LineChart, // динамика, прогноз и коридор
  BarChart, // топы
  GridComponent, // оси и сетка
  TooltipComponent, // подсказка при наведении
  LegendComponent, // легенда: клик прячет и показывает ряд
  DataZoomComponent, // приближение: колесо, щипок, ползунок
  ToolboxComponent, // кнопки "сбросить приближение" и "скачать PNG"
  MarkLineComponent, // вертикальная черта "сегодня" на графике прогноза
  AriaComponent, // описание графика для экранного диктора
  CanvasRenderer,
]);

// Русские подписи кнопок и подсказок самого ECharts
echarts.registerLocale('RU', langRU);

export { echarts };
export const ECHARTS_LOCALE = 'RU';
