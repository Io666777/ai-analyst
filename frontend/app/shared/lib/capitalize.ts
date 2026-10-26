/**
 * Первая буква - заглавная: сервер присылает «август 2026», в начале строки нужно «Август 2026».
 * @param {string} text - текст.
 * @returns {string} текст с заглавной буквы.
 */
export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}
