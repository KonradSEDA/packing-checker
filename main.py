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

    # Zaktualizowane zapytanie SQL zgodnie z Twoim wymaganiem
    query = """
        SELECT * 
        FROM `bazadanycherpwannabe.Overview.PackingOverview` 
        WHERE orderNumber IN (
            SELECT orderNumber 
            FROM `bazadanycherpwannabe.Overview.PackingOverview` 
            WHERE barcode = @barcode_val
        )
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("barcode_val", "STRING", str(barcode_val))
        ]
    )

    try:
        query_job = bq_client.query(query, job_config=job_config)
        results = [dict(row) for row in query_job.result()] # Konwersja wyników na słowniki JSON

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