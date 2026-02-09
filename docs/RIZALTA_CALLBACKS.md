# Callback Data Index — RIZALTA Bot v2.5.10

> Полный индекс всех callback_data паттернов.
> Формат: `callback_data` → обработчик → файл

## Корпус 3

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `c3_*` | `handle_corp3_callback` | `handlers/corp3.py` |
| `c3_menu` | `handle_corp3_start` | `handlers/corp3.py` |
| `c3_by_rooms` | `handle_corp3_by_rooms` | `handlers/corp3.py` |
| `c3_by_floor` | `handle_corp3_by_floor` | `handlers/corp3.py` |
| `c3_by_area` | `handle_corp3_by_area` | `handlers/corp3.py` |
| `c3_by_code` | `handle_corp3_by_code` | `handlers/corp3.py` |
| `c3_all_{offset}` | `handle_corp3_show_list` | `handlers/corp3.py` |
| `c3_floor_{N}_{offset}` | `handle_corp3_show_list` | `handlers/corp3.py` |
| `c3_lot_{code}` | `handle_corp3_lot_detail` | `handlers/corp3.py` |
| `c3_kp12_{code}` | `handle_corp3_generate_kp` | `handlers/corp3.py` |
| `c3_kp18_{code}` | `handle_corp3_generate_kp` | `handlers/corp3.py` |
| `c3_layout_{code}` | `handle_corp3_layout` | `handlers/corp3.py` |

## КП и навигация по лотам

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `kp_menu` | `handle_kp_menu` | `handlers/kp.py` |
| `kp_refine` | (показывает уточнение) | `app.py` |
| `kp_by_building` | `handle_kp_by_building_menu` | `handlers/kp.py` |
| `kp_building_all_{N}` | `handle_kp_building_all` | `handlers/kp.py` |
| `kp_building_{N}` | `handle_kp_building` | `handlers/kp.py` |
| `kp_floors_{b}_{range}` | `handle_kp_floors_range` | `handlers/kp.py` |
| `kp_floor_all_{b}_{f}` | (показывает все лоты этажа) | `app.py` |
| `kp_floor_{b}_{f}` | `handle_kp_floor` | `handlers/kp.py` |
| `kp_lot_{code}` | `handle_kp_lot` | `handlers/kp.py` |
| `kp_gen_{code}_{b}_{mode}` | `handle_kp_generate` | `handlers/kp.py` |
| `kp_by_code` | `handle_kp_by_code_menu` | `handlers/kp.py` |
| `kp_show_more` | `handle_kp_show_more` | `handlers/kp.py` |
| `kp_by_area` | `handle_kp_by_area_menu` | `handlers/kp.py` |
| `kp_by_budget` | `handle_kp_by_budget_menu` | `handlers/kp.py` |
| `kp_area_{min}_{max}` | `handle_kp_area_range` | `handlers/kp.py` |
| `kp_budget_{min}_{max}` | `handle_kp_budget_range` | `handlers/kp.py` |
| `kp_show_area_{min}_{max}_{offset}` | `handle_kp_show_all_area` | `handlers/kp.py` |
| `kp_show_budget_{min}_{max}` | `handle_kp_show_all_budget` | `handlers/kp.py` |
| `kp_send_{mode}` | (отправка КП) | `app.py` |
| `kp_select_{area_x10}` | `handle_kp_select_lot` | `handlers/kp.py` |

## Навигация для расчётов (calc_nav_*)

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `calc_nav_menu` | `handle_nav_menu(mode="calc")` | `handlers/kp.py` |
| `calc_nav_by_building` | `handle_nav_by_building_menu(mode="calc")` | `handlers/kp.py` |
| `calc_nav_building_all_{N}` | `handle_kp_building_all` | `handlers/kp.py` |
| `calc_nav_building_{N}` | `handle_nav_building(mode="calc")` | `handlers/kp.py` |
| `calc_nav_floors_{b}_{range}` | `handle_kp_floors_range` | `handlers/kp.py` |
| `calc_nav_floor_{b}_{f}` | `handle_nav_floor(mode="calc")` | `handlers/kp.py` |
| `calc_nav_lot_{code}_{b}` | `handle_nav_lot(mode="calc")` | `handlers/kp.py` |
| `calc_nav_by_area` | `handle_kp_by_area_menu` | `handlers/kp.py` |
| `calc_nav_by_budget` | `handle_kp_by_budget_menu` | `handlers/kp.py` |
| `calc_nav_by_code` | `handle_kp_by_code_menu` | `handlers/kp.py` |

## Навигация для сравнения (compare_nav_*)

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `compare_nav_menu` | `handle_nav_menu(mode="compare")` | `handlers/kp.py` |
| `compare_nav_by_building` | `handle_nav_by_building_menu(mode="compare")` | `handlers/kp.py` |
| `compare_nav_building_all_{N}` | `handle_kp_building_all` | `handlers/kp.py` |
| `compare_nav_building_{N}` | `handle_nav_building(mode="compare")` | `handlers/kp.py` |
| `compare_nav_floors_{b}_{range}` | `handle_kp_floors_range` | `handlers/kp.py` |
| `compare_nav_floor_{b}_{f}` | `handle_nav_floor(mode="compare")` | `handlers/kp.py` |
| `compare_nav_lot_{code}_{b}` | `handle_nav_lot(mode="compare")` | `handlers/kp.py` |
| `compare_nav_by_area` | `handle_kp_by_area_menu` | `handlers/kp.py` |
| `compare_nav_by_budget` | `handle_kp_by_budget_menu` | `handlers/kp.py` |
| `compare_nav_by_code` | `handle_kp_by_code_menu` | `handlers/kp.py` |

## Расчёт доходности

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `calc_main_menu` | `handle_calculations_menu_new` | `handlers/calc_dynamic.py` |
| `calc_roi_menu` | `handle_calc_roi_menu` | `handlers/calc_dynamic.py` |
| `calc_finance_menu` | `handle_calc_finance_menu` | `handlers/calc_dynamic.py` |
| `calc_roi_by_area` | `handle_calc_roi_by_area_menu` | `handlers/calc_dynamic.py` |
| `calc_roi_by_budget` | `handle_calc_roi_by_budget_menu` | `handlers/calc_dynamic.py` |
| `calc_finance_by_area` | `handle_calc_finance_by_area_menu` | `handlers/calc_dynamic.py` |
| `calc_finance_by_budget` | `handle_calc_finance_by_budget_menu` | `handlers/calc_dynamic.py` |
| `calc_roi_area_{min}_{max}` | `handle_calc_roi_area_range` | `handlers/calc_dynamic.py` |
| `calc_roi_budget_{min}_{max}` | `handle_calc_roi_budget_range` | `handlers/calc_dynamic.py` |
| `calc_roi_show_area_{min}_{max}` | `handle_calc_roi_show_all_area` | `handlers/calc_dynamic.py` |
| `calc_roi_show_budget_{min}_{max}` | `handle_calc_roi_show_all_budget` | `handlers/calc_dynamic.py` |
| `calc_fin_show_area_{min}_{max}` | `handle_calc_finance_show_all_area` | `handlers/calc_dynamic.py` |
| `calc_fin_show_budget_{min}_{max}` | `handle_calc_finance_show_all_budget` | `handlers/calc_dynamic.py` |
| `calc_fin_area_{min}_{max}` | `handle_calc_finance_area_range` | `handlers/calc_dynamic.py` |
| `calc_fin_budget_{min}_{max}` | `handle_calc_finance_budget_range` | `handlers/calc_dynamic.py` |
| `calc_roi_code_{code}_{b}` | `handle_calc_roi_by_code` | `handlers/calc_dynamic.py` |
| `calc_finance_code_{code}_{b}` | `handle_calc_finance_by_code` | `handlers/calc_dynamic.py` |
| `calc_roi_lot_{area}` | `handle_calc_roi_lot` | `handlers/calc_dynamic.py` |
| `calc_finance_lot_{area}` | `handle_calc_finance_lot` | `handlers/calc_dynamic.py` |
| `roi_xlsx_code_{code}_{b}` | `generate_roi_xlsx` | `services/calc_xlsx_generator.py` |
| `roi_xlsx_{area}` | `generate_roi_xlsx` | `services/calc_xlsx_generator.py` |
| `roi_{area}` | `handle_base_roi` | `handlers/units.py` |

## Сравнение с депозитом

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `compare_menu` | `handle_compare_menu` | `handlers/compare.py` |
| `compare_by_area` | `handle_compare_by_area_menu` | `handlers/compare.py` |
| `compare_by_budget` | `handle_compare_by_budget_menu` | `handlers/compare.py` |
| `compare_quick` | `handle_compare_quick` | `handlers/compare.py` |
| `compare_area_{min}_{max}` | `handle_compare_area_range` | `handlers/compare.py` |
| `compare_budget_{min}_{max}` | `handle_compare_budget_range` | `handlers/compare.py` |
| `compare_lot_{code}_{b}_{price}_{area10}` | `handle_compare_lot` | `handlers/compare.py` |
| `compare_lot_back_{amount}_{area10}` | (возврат к выбору периода) | `app.py` |
| `compare_period_{years}_{amount}_{area10}` | `handle_compare_period` | `handlers/compare.py` |
| `compare_full_{years}_{amount}_{area10}` | `handle_compare_full` | `handlers/compare.py` |
| `compare_table_{amount}_{area10}` | `handle_compare_table` | `handlers/compare.py` |
| `compare_table` | `handle_compare_table` | `handlers/compare.py` |
| `compare_amount_{context}` | `handle_compare_amount_menu` | `handlers/compare.py` |
| `compare_sum_{amount}_{context}` | `handle_compare_with_amount` | `handlers/compare.py` |
| `compare_pdf_{years}_{amount}_{area10}` | `handle_compare_pdf` | `handlers/compare.py` |

## Ипотека (только DEV)

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `mortgage_{code}_{b}` | `handle_mortgage_menu` | `handlers/mortgage.py` |
| `mort_{tariff}_{code}_{b}_{dp}_{term}` | `handle_mortgage_menu` | `handlers/mortgage.py` |
| `mort_pdf_{tariff}_{code}_{b}_{dp}_{term}` | `handle_mortgage_pdf` | `handlers/mortgage.py` |

## Бронирование

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `select_lot` | `handle_select_lot` | `handlers/units.py` |
| `call_manager` / `online_show` | `handle_online_show_start` | `handlers/booking.py` |
| `booking_calendar` | `handle_booking_start` | `handlers/booking_calendar.py` |
| `book_date_{date}` | `handle_select_date` | `handlers/booking_calendar.py` |
| `book_time_{time}` | `handle_select_time` | `handlers/booking_calendar.py` |
| `book_time_confirmed` | `handle_time_confirmed` | `handlers/booking_calendar.py` |
| `book_tz_moscow` / `book_tz_altai` | `handle_select_timezone` | `handlers/booking_calendar.py` |
| `book_change_tz` | `handle_change_timezone` | `handlers/booking_calendar.py` |
| `book_set_tz_{tz}` | `handle_set_timezone` | `handlers/booking_calendar.py` |
| `book_add_phone` | `handle_request_phone` | `handlers/booking_calendar.py` |
| `book_submit` | `handle_submit_booking` | `handlers/booking_calendar.py` |
| `book_edit_menu` | `handle_edit_menu` | `handlers/booking_calendar.py` |
| `book_take_{id}` | `handle_take_booking` | `handlers/booking_calendar.py` |
| `booking_menu` | `handle_booking_menu` | `handlers/booking_fixation.py` |
| `booking_auth` | `handle_booking_auth_start` | `handlers/booking_fixation.py` |
| `booking_reauth` | `handle_booking_reauth` | `handlers/booking_fixation.py` |
| `booking_new` | `handle_booking_new` | `handlers/booking_fixation.py` |
| `booking_cancel` | `handle_booking_cancel` | `handlers/booking_fixation.py` |
| `booking_skip_comment` | `handle_booking_skip_comment` | `handlers/booking_fixation.py` |

## Меню и навигация

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `back_to_menu` | `handle_back` | `handlers/menu.py` |
| `calculate_roi` | `handle_choose_unit_for_roi` | `handlers/menu.py` |
| `get_layouts` | `handle_choose_unit_for_layout` | `handlers/menu.py` |

## Медиа

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `media_menu` | `handle_media_menu` | `handlers/media.py` |
| `media_presentation` | `handle_send_presentation` | `handlers/media.py` |
| `media_video` | `handle_video_menu` | `handlers/media.py` |
| `pres_{key}` | `handle_send_presentation_file` | `handlers/media.py` |
| `video_{key}` | `handle_send_video` | `handlers/media.py` |

## Документы

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `doc_menu` | `handle_documents_menu` | `handlers/docs.py` |
| `doc_ddu` | `handle_send_ddu` | `handlers/docs.py` |
| `doc_arenda` | `handle_send_arenda` | `handlers/docs.py` |
| `doc_all` | `handle_send_all_docs` | `handlers/docs.py` |

## Секретарь

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `secretary_menu` | `handle_secretary_menu` | `handlers/secretary.py` |
| `sec_day_{date}` | `handle_secretary_day` | `handlers/secretary.py` |
| `sec_week_{date}` | `handle_secretary_week` | `handlers/secretary.py` |
| `sec_task_{id}` | `handle_secretary_task_detail` | `handlers/secretary.py` |
| `sec_done_{id}` | `handle_secretary_done` | `handlers/secretary.py` |
| `sec_undone_{id}` | `handle_secretary_undone` | `handlers/secretary.py` |
| `sec_del_{id}` | `handle_secretary_delete` | `handlers/secretary.py` |
| `sec_move_{id}` | `handle_secretary_move_menu` | `handlers/secretary.py` |
| `sec_moveto_{id}_{date}` | `handle_secretary_move_to` | `handlers/secretary.py` |
| `sec_add` | `handle_secretary_add_prompt` | `handlers/secretary.py` |
| `sec_timezone` | `handle_timezone_menu` | `handlers/secretary.py` |
| `sec_set_tz_{tz}` | `handle_set_timezone` | `handlers/secretary.py` |
| `sec_add_{date}` | `handle_secretary_add_prompt` | `handlers/secretary.py` |

## Новости

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `news_menu` | `handle_news_menu` | `handlers/news.py` |
| `news_currency` | `handle_currency_rates` | `handlers/news.py` |
| `news_weather` | `handle_weather` | `handlers/news.py` |
| `news_digest` | `handle_news_digest` | `handlers/news.py` |
| `news_flights` | `handle_flights` | `handlers/news.py` |

## Домопланер

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `domo_all` | (показывает все лоты из домопланера) | `app.py` |
| `domo_{code}` | `handle_domoplaner_select` | `handlers/domoplaner.py` |

## Layout

| Callback | Обработчик | Файл |
|----------|-----------|------|
| `layout_{code}` | (отправка планировки) | `app.py` |
| `finance_{code}` | `handle_finance_overview` | `handlers/units.py` |

## Важные паттерны кодирования в callback_data

```
# Площадь кодируется как area10 = int(area_m2 * 10) для экономии байт
compare_lot_В615_1_14300_220    → code=В615, building=1, price=14300(тыс), area10=220 (=22.0 м²)
compare_period_3_14452000_235   → years=3, amount=14452000, area10=235 (=23.5 м²)

# Обратная совместимость: если area10 отсутствует → дефолт 26.8 м²
```
