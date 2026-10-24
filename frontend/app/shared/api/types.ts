// Короткие имена для типов ответов API. Сами типы генерируются из Swagger (schema.d.ts):
// поменяли ответ ручки на бэке -> npm run api:types -> TypeScript покажет, что поправить во фронте
import type { components } from './schema';

type Schemas = components['schemas'];

// ---------- загрузка и настройка ----------
export type FileOpened = Schemas['FileOpened'];
export type ColumnPreview = Schemas['ColumnPreview'];
export type Options = Schemas['Options'];
export type Choice = Schemas['Choice'];
export type MappingRequest = Schemas['MappingRequest'];
export type PreparedData = Schemas['PreparedData'];
export type PreparationReport = Schemas['PreparationReport'];
export type SettingsRequest = Schemas['SettingsRequest'];
export type SettingsApplied = Schemas['SettingsApplied'];

// ---------- анализ ----------
export type SeriesPoint = Schemas['SeriesPoint'];
export type MonthSummary = Schemas['MonthSummary'];
export type Overview = Schemas['Overview'];
export type Daily = Schemas['Daily'];
export type Top = Schemas['Top'];
export type TopRow = Schemas['TopRow'];
export type ItemsFound = Schemas['ItemsFound'];
export type ItemDetail = Schemas['ItemDetail'];
export type ItemDays = Schemas['ItemDays'];
export type ItemDay = Schemas['ItemDay'];
export type Comparison = Schemas['Comparison'];
export type CompareRow = Schemas['CompareRow'];
export type PeriodTotal = Schemas['PeriodTotal'];
export type Forecast = Schemas['Forecast'];
export type ForecastPoint = Schemas['ForecastPoint'];
export type Accuracy = Schemas['Accuracy'];
export type Estimate = Schemas['Estimate'];
