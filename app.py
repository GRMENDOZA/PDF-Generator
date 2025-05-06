from flask import Flask, request, make_response, jsonify
import json
import fitz  # PyMuPDF

app = Flask(__name__)

def getErrorResponse(error):
    jsonRaw = {
        "fulfillmentResponse": {
            "messages": [
                {
                    "text": {
                        "text": [
                            '{}'.format(error)
                        ]
                    }
                }
            ]
        }
    }
    return app.response_class(
        response=json.dumps(jsonRaw, ensure_ascii=False),
        status=400,
        mimetype='application/json'
    )

def insert_text_wrapped(page, text, x, y, max_chars=50, line_height=12, fontsize=10):
    """
    Inserta texto en el PDF dividiendo automáticamente en líneas cuando se alcanza el máximo de caracteres.
    """
    lines = []
    for line in text.split("\n"):
        while len(line) > max_chars:
            split_at = line.rfind(" ", 0, max_chars)
            if split_at == -1:
                split_at = max_chars
            lines.append(line[:split_at])
            line = line[split_at:].lstrip()
        lines.append(line)

    for i, line in enumerate(lines):
        page.insert_text((x, y + i * line_height), line, fontsize=fontsize)

def fillPDF(data):
    # Cargar el PDF base
    doc = fitz.open("FormatoCliente.pdf")
    page = doc[0]

    # Get and Fill information from ShippingDetails Header
    try:
        origenDestination = data.get("ShippingDetails").get("OriginDestination", "").split("-")
        origen = origenDestination[0].strip()
        destination = origenDestination[1].strip()
    except:
        origen = data.get("ShippingDetails").get("OriginDestination", "")
        destination = data.get("ShippingDetails").get("OriginDestination", "")

    insert_text_wrapped(page, origen, 62, 136)
    insert_text_wrapped(page, destination, 62, 170)
    insert_text_wrapped(page, data.get("ShippingDetails").get("Date", ""), 210, 160)
    insert_text_wrapped(page, data.get("ShippingDetails").get("Series", ""), 320, 160, max_chars=18, fontsize=8)
    insert_text_wrapped(page, data.get("ShippingDetails").get("OriginDestination", ""), 430, 160)

    # Sender
    insert_text_wrapped(page, data.get("Sender").get("Client", ""), 73, 225, max_chars=40)
    insert_text_wrapped(page, data.get("Sender").get("Name", ""), 73, 275,max_chars=40)
    insert_text_wrapped(page, data.get("Sender").get("Address", ""), 73, 320,max_chars=40)
    insert_text_wrapped(page, data.get("Sender").get("Colony", ""), 73, 365,max_chars=40)
    insert_text_wrapped(page, data.get("Sender").get("PostalCode", ""), 73, 412,max_chars=40)
    insert_text_wrapped(page, data.get("Sender").get("CityState", ""), 73, 457,max_chars=40)
    insert_text_wrapped(page, data.get("Sender").get("Country", ""), 73, 502,max_chars=40)
    insert_text_wrapped(page, data.get("Sender").get("Phone", ""), 73, 547,max_chars=40)

    # Recipient
    insert_text_wrapped(page, data.get("Recipient").get("Client", ""), 339, 230,max_chars=40)
    insert_text_wrapped(page, data.get("Recipient").get("Name", ""), 339, 275,max_chars=40)
    insert_text_wrapped(page, data.get("Recipient").get("Address", ""), 339, 320,max_chars=40)
    insert_text_wrapped(page, data.get("Recipient").get("Colony", ""), 339, 365,max_chars=40)
    insert_text_wrapped(page, data.get("Recipient").get("PostalCode", ""), 339, 412,max_chars=40)
    insert_text_wrapped(page, data.get("Recipient").get("CityState", ""), 339, 457,max_chars=40)
    insert_text_wrapped(page, data.get("Recipient").get("Country", ""), 339, 502,max_chars=40)
    insert_text_wrapped(page, data.get("Recipient").get("Phone", ""), 339, 547,max_chars=40)

    # Tipo de paquete
    typeForm = data.get("PackageInfo", {}).get("Type", "").lower()
    if typeForm == 'sobre':
        xTypeForm, yTypeForm = 40, 600
    elif typeForm == 'caja':
        xTypeForm, yTypeForm = 95, 600
    elif typeForm == 'valija':
        xTypeForm, yTypeForm = 148, 600
    elif typeForm == 'tarima':
        xTypeForm, yTypeForm = 206, 600
    else:
        xTypeForm, yTypeForm = 280, 600

    page.insert_text((xTypeForm, yTypeForm), 'X', fontsize=10)

    # Medidas
    page.insert_text((92, 645), str(data.get("PackageInfo").get("Width", "")), fontsize=10)
    page.insert_text((146, 645), str(data.get("PackageInfo").get("Height", "")), fontsize=10)
    page.insert_text((204, 645), str(data.get("PackageInfo").get("Length", "")), fontsize=10)
    page.insert_text((272, 645), str(data.get("PackageInfo").get("Volume", "")), fontsize=10)
    page.insert_text((367, 645), str(data.get("PackageInfo").get("Weight", "")), fontsize=10)

    # No. de rastreo y referencia
    insert_text_wrapped(page, data.get("ShippingDetails").get("TrackingNumber", ""), 430, 600, max_chars=20, line_height=10)
    insert_text_wrapped(page, data.get("CommittedBy", ""), 434, 645, max_chars=30, fontsize=8, line_height=10)

    # Observaciones
    insert_text_wrapped(page, data.get("Observations", ""), 92, 680, max_chars=60)

    # Guardar en memoria
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

@app.route("/generate-pdf", methods=["POST", "GET"])
def generate_pdf():
    try:
        data = request.get_json()
        if not data:
            return getErrorResponse("Not Json Data")

        pdf_bytes = fillPDF(data)

        response = make_response(pdf_bytes)
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'inline', filename='FormatoCliente_Llenado.pdf')
        return response

    except Exception as e:
        return getErrorResponse("An error occurred: " + str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
