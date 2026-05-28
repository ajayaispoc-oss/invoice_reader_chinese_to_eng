import logging
import os
import json
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import azure.functions as func
from models import CorporateInvoiceSchema
# Initialize the Function App worker framework
app = func.FunctionApp()

@app.blob_trigger(
    arg_name="myblob", 
    path="input-invoices/{name}.pdf", 
    connection="AzureWebJobsStorage"
)
def invoice_routing_processor(myblob: func.InputStream):
    logging.info(f"Processing invoice blob: {myblob.name} ({myblob.length} bytes)")

    # Read the raw Chinese PDF file stream
    pdf_bytes = myblob.read()
    
    try:
        # --- PHASE A: Multi-lingual OCR Extraction ---
        doc_intel_client = DocumentIntelligenceClient(
            endpoint=os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"],
            credential=AzureKeyCredential(os.environ["DOCUMENT_INTELLIGENCE_KEY"])
        )
        
        # 'prebuilt-layout' accurately maps character boundaries for Simplified/Traditional Chinese
        poller = doc_intel_client.begin_analyze_document(
            "prebuilt-layout", 
            body=pdf_bytes, 
            content_type="application/pdf"
        )
        ocr_result = poller.result()
        
        # Build unstructured text block from lines
        extracted_text = ""
        if ocr_result.pages:
            for page in ocr_result.pages:
                for line in page.lines:
                    extracted_text += line.content + "\n"

        logging.info("Phase A complete: Document text extracted via OCR.")

        # --- PHASE B: AI Translation & Structural Parsing ---
        openai_client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version="2024-08-01-preview"
        )

        system_prompt = (
            "You are an AI financial auditor. Extract data from Chinese invoice text, "
            "translate descriptive values to standard English financial terms, and strictly "
            "comply with the target JSON schema structure."
        )

        # Force structural matching through Pydantic parser bindings
        completion = openai_client.beta.chat.completions.parse(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract details from this invoice:\n{extracted_text}"}
            ],
            response_format=CorporateInvoiceSchema
        )

        invoice_data = completion.choices[0].message.parsed
        logging.info(f"Phase B complete: Extracted Invoice ID: {invoice_data.invoice_id}, PO Number: {invoice_data.po_number}")

        # --- PHASE C: Conditional Business Routing & Storage Commits ---
        # Normalize fields for programmatic checks
        po_str = invoice_data.po_number.strip().lower()
        inv_id = invoice_data.invoice_id.strip()
        
        # Determine file naming route based on business rule criteria
        if po_str.startswith("po"):
            target_filename = f"{inv_id}_po.json"
        elif po_str.startswith("ap"):
            target_filename = f"{inv_id}_ap.json"
        else:
            target_filename = f"{inv_id}_default.json"
            logging.warning(f"PO number '{invoice_data.po_number}' did not match 'po' or 'ap' routing prefixes.")

        # Serialize Pydantic object structure back to a formatted json string
        json_output_payload = invoice_data.model_dump_json(indent=4)

        # Connect to destination blob store
        blob_service_client = BlobServiceClient.from_connection_string(os.environ["SourceBlobConnectionString"])
        output_blob_client = blob_service_client.get_blob_client(
            container="output-data",
            blob=target_filename
        )
        
        # Upload the JSON file to your destination directory container
        output_blob_client.upload_blob(json_output_payload, overwrite=True)
        logging.info(f"Phase C complete: Successfully routed and uploaded file to output-directory/{target_filename}")

    except Exception as error:
        logging.error(f"Failed to process and route document pipeline: {str(error)}")
        raise error
