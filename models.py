from pydantic import BaseModel, Field

class CorporateInvoiceSchema(BaseModel):
    """Enforces strict extraction and mapping rules for Chinese Invoices."""
    invoice_id: str = Field(description="The unique alphanumeric identifier/invoice number (发票号码).")
    date: str = Field(description="The date of invoice issuance (开票日期) formatted as YYYY-MM-DD.")
    due_date: str = Field(description="The payment due date (到期日/付款截止日) formatted as YYYY-MM-DD.")
    po_number: str = Field(description="The Purchase Order number (采购订单号). Force lowercase letters (e.g. convert 'PO123' or 'po123' to 'po123'). If missing, return an empty string.")
    terms: str = Field(description="The payment terms or conditions (付款条件/条款), translated into English (e.g., Net 30, Due on Receipt).")
