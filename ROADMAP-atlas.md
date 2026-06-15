# ROADMAP — Tích hợp Atlas làm nguồn dữ liệu (SAU cuộc thi)

> ⚠️ **Chỉ làm SAU Claw-a-thon 2026.** Trong cuộc thi, thể lệ cấm dùng hệ thống nội bộ/production
> (`atlas.vng.com.vn` là nội bộ VNG). Bản dự thi giữ nguyên luồng upload CSV/Excel.

## Mục tiêu
Thay vì upload CSV thủ công, agent đọc thẳng dữ liệu merchant từ **atlas.vng.com.vn** → phân tích tự động,
refresh định kỳ. Hướng tới công cụ AM dùng hằng ngày.

## Nguyên tắc thiết kế: ĐA NGUỒN, ít sửa code
Code hiện tại đã tách sạch. Điểm chèn duy nhất là **trước `MerchantAnalyzer`**:

```
[Atlas API/DB] → connector → DataFrame (chuẩn 11 cột) → MerchantAnalyzer (GIỮ NGUYÊN) → llm → answer
```

`load_dataframe()` (pipeline.py) đã chuẩn hóa + validate 11 cột. Connector chỉ cần **trả DataFrame đúng schema**
là toàn bộ pipeline + LLM chạy y nguyên — không viết lại logic phân tích.

### Interface đề xuất
```python
class DataSource:                      # abstract
    def fetch(self, filters) -> pd.DataFrame: ...

class CsvSource(DataSource):  ...      # giữ cho demo/cá nhân (luồng hiện tại)
class AtlasSource(DataSource): ...     # production: token + query → DataFrame chuẩn
```
Cả hai trả về cùng schema 11 cột (`merchant_id, merchant_name, category, region, week_start,
transaction_count, revenue_vnd, gross_profit_vnd, unique_customers, returning_customers, avg_order_value_vnd`).

## Quyết định then chốt: Atlas expose dữ liệu kiểu gì?
| Atlas cung cấp | Cách tích hợp | Ưu tiên |
|---|---|---|
| **API/REST** (có token) | Gọi API → DataFrame | ⭐ Tốt nhất |
| **DB / Data warehouse** (atlas chỉ là UI) | Kết nối nguồn (Presto/Trino/MySQL…) bằng SQL | ⭐⭐ |
| **Chỉ UI / export** | Export CSV định kỳ; scrape là phương án cuối (kém bền) | ⭐⭐⭐ Tránh |

→ **Việc đầu tiên cần xác minh:** atlas có API/DB truy cập được không, hay chỉ có UI.

## Hạng mục kỹ thuật (sau thi)
1. **Auth nội bộ** — SSO / service account / token. Lưu trong secret manager, KHÔNG hardcode/commit.
2. **Mạng** — agent phải nằm trong mạng nội bộ hoặc qua VPN/private endpoint (atlas không public).
3. **Mapping schema** — map cột atlas → 11 cột chuẩn; có thể cần file config mapping.
4. **Caching + phân trang** — data lớn → cache theo kỳ, query incremental thay vì kéo full mỗi lần.
5. **Phân quyền (row-level)** — AM chỉ thấy merchant trong danh mục của mình.
6. **Refresh tự động / scheduled** — cron pull thay vì upload tay; có thể realtime nếu atlas hỗ trợ.
7. **Quan sát** — log nguồn dữ liệu, thời điểm refresh, số dòng, để debug khi số liệu lệch.

## Lưu ý bảo mật
- Không dán cookie/token nội bộ vào chat, code, hay commit.
- Tuân thủ chính sách dữ liệu nội bộ VNG khi truy cập dữ liệu merchant thật.
