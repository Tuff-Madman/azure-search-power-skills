import logging
import json
import os
import logging
import datetime
from json import JSONEncoder
import azure.functions as func
from azure.ai.formrecognizer import FormRecognizerClient
from azure.ai.formrecognizer import FormTrainingClient
from azure.core.credentials import AzureKeyCredential

class DateTimeEncoder(JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()

def main(req: func.HttpRequest) -> func.HttpResponse:
        logging.info('Invoked AnalyzeInvoice Skill.')
        try:
                if body := json.dumps(req.get_json()):
                        logging.info(body)
                        result = compose_response(body)
                        return func.HttpResponse(result, mimetype="application/json")
                else:
                        return func.HttpResponse(
                            "Invalid body",
                            status_code=400
                        )
        except ValueError:
            return func.HttpResponse(
                 "Invalid body",
                 status_code=400
            )
def compose_response(json_data):
        values = json.loads(json_data)['values']

            # Prepare the Output before the loop
        results = {"values": []}
        endpoint = os.environ["FORMS_RECOGNIZER_ENDPOINT"]
        key = os.environ["FORMS_RECOGNIZER_KEY"]
        form_recognizer_client = FormRecognizerClient(endpoint, AzureKeyCredential(key))
        for value in values:
            output_record = transform_value(value, form_recognizer_client)
            if output_record != None:
                results["values"].append(output_record)
        return json.dumps(results, ensure_ascii=False, cls=DateTimeEncoder)

## Perform an operation on a record
def transform_value(value, form_recognizer_client):
        try:
            recordId = value['recordId']
        except AssertionError  as error:
            return None
            # Validate the inputs
        try: 
                assert ('data' in value), "'data' field is required."
                data = value['data']
                print(data)
                form_url = data["formUrl"]  + data["formSasToken"]
                print(form_url)
                poller = form_recognizer_client.begin_recognize_invoices_from_url(form_url)
                invoices = poller.result()
                invoiceResults = []

                for invoice in invoices:
                        invoiceResult = {}
                        if amount_due := invoice.fields.get("AmountDue"):
                                invoiceResult["AmountDue"] = amount_due.value
                        if billing_address := invoice.fields.get(
                            "BillingAddress"):
                                invoiceResult["BillingAddress"] = billing_address.value
                        if billing_address_recipient := invoice.fields.get(
                            "BillingAddressRecipient"):
                                invoiceResult["BillingAddressRecipient"] = billing_address_recipient.value
                        if customer_address := invoice.fields.get(
                            "CustomerAddress"):
                                invoiceResult["CustomerAddress"] = customer_address.value
                        if customer_address_recipient := invoice.fields.get(
                            "CustomerAddressRecipient"):
                                invoiceResult["CustomerAddressRecipient"] = customer_address_recipient.value
                        if due_date := invoice.fields.get("DueDate"):
                                invoiceResult["DueDate"] = due_date.value
                        if invoice_date := invoice.fields.get("InvoiceDate"):
                                invoiceResult["InvoiceDate"] = invoice_date.value
                        if invoice_id := invoice.fields.get("InvoiceId"):
                                invoiceResult["InvoiceId"] = invoice_id.value
                        if invoice_total := invoice.fields.get("InvoiceTotal"):
                                invoiceResult["InvoiceTotal"] = invoice_total.value
                        if vendor_address := invoice.fields.get(
                            "VendorAddress"):
                                invoiceResult["VendorAddress"] = vendor_address.value
                        if vendor_name := invoice.fields.get("VendorName"):
                                invoiceResult["VendorName"] = vendor_name.value
                        sub_total = invoice.fields.get("SubTotal")
                        if sub_total:
                            invoiceResult["SubTotal"] = sub_total.value
                        total_tax = invoice.fields.get("TotalTax")
                        if sub_total:
                            invoiceResult["TotalTax"] = total_tax.value

                        invoiceResults.append(invoiceResult)
        except AssertionError as error:
                return {
                    "recordId": recordId,
                    "errors": [{
                        "message": f"Error:{error.args[0]}"
                    }],
                }
        except Exception as error:
                return {"recordId": recordId, "errors": [{"message": f"Error:{str(error)}"}]}
        return ({
                "recordId": recordId,   
                "data": {
                    "invoices": invoiceResults
                }
                })
