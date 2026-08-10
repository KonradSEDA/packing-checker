import functions_framework
from google.cloud import bigquery
from flask import jsonify

bq_client = bigquery.Client()

@functions_framework.http
def check_order(request):
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    request_json = request.get_json(silent=True)
    request_args = request.args

    barcode_val = None
    if request_json and 'barcode' in request_json:
        barcode_val = request_json['barcode']
    elif request_args and 'barcode' in request_args:
        barcode_val = request_args['barcode']

    if not barcode_val:
        return jsonify({"error": "Brak kodu w żądaniu"}), 400, headers

    # Jawne rzutowanie orderNumber na STRING w zapytaniu unika konfliktów typów
    query = """
        SELECT * 
        FROM `bazadanycherpwannabe.Overview.PackingOverview` 
        WHERE CAST(orderNumber AS STRING) IN (
            SELECT CAST(orderNumber AS STRING)
            FROM `bazadanycherpwannabe.Overview.PackingOverview` 
            WHERE barcode = @barcode_val
        )
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("barcode_val", "STRING", str(barcode_val).strip())
        ]
    )

    try:
        query_job = bq_client.query(query, job_config=job_config)
        
        results = []
        for row in query_job.result():
            row_dict = dict(row)
            # Konwersja pól typu datetime/date do stringa, żeby Flask / jsonify się nie wyłożył
            for key, val in row_dict.items():
                if hasattr(val, 'isoformat'):
                    row_dict[key] = val.isoformat()
            results.append(row_dict)

        if results:
            return jsonify({
                "status": "found",
                "items": results
            }), 200, headers
        else:
            return jsonify({
                "status": "not_found",
                "message": f"Nie znaleziono zamówienia dla kodu {barcode_val}"
            }), 404, headers

    except Exception as e:
        return jsonify({"error": str(e)}), 500, headers