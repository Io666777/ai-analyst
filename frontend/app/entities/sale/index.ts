// Публичный вход слайса entities/sale: запросы продаж, нужные нескольким разделам
// (топ за период - топу и обзору, дни периода - обзору)
export { fetchDaily } from './api/daily-api';
export { fetchTop, type TopRequest } from './api/top-api';
