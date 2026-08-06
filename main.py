import functions_framework
from google.cloud import bigquery
from flask import jsonify

# Inicjalizacja klienta BigQuery (sam pobierze uprawnienia z chmury)
bq_client = bigquery.Client()

@functions_framework.http
def check_order(request):
    # Obsługa nagłówków CORS, żeby telefon nie blokował zapytań
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    # Pobieramy dane z żądania (obsługujemy zarówno parametry URL, jak i JSON)
    request_json = request.get_json(silent=True)
    request_args = request.args

    order_number = None
    if request_json and 'orderNumber' in request_json:
        order_number = request_json['orderNumber']
    elif request_args and 'orderNumber' in request_args:
        order_number = request_args['orderNumber']

    if not order_number:
        return jsonify({"error": "Brak numeru zamówienia w żądaniu"}), 400, headers

    try:
        # Konwersja na int, żeby zabezpieczyć zapytanie
        order_int = int(order_number)
    except ValueError:
        return jsonify({"error": "Nieprawidłowy format numeru zamówienia (musi być liczba)"}), 400, headers

    # Twoje zapytanie SQL do BigQuery
    query = """
        SELECT orderNumber 
        FROM `bazadanycherpwannabe.Overview.PackingOverview` 
        WHERE orderNumber = @order_number
        LIMIT 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("order_number", "INT64", order_int)
        ]
    )

    try:
        query_job = bq_client.query(query, job_config=job_config)
        results = list(query_job.result())

        if results:
            # Zamówienie znalezione
            row = results[0]
            return jsonify({
                "status": "found",
                "orderNumber": row["orderNumber"]
            }), 200, headers
        else:
            # Brak zamówienia w bazie
            return jsonify({
                "status": "not_found",
                "message": f"Nie znaleziono zamówienia o numerie {order_int}"
            }), 404, headers

    except Exception as e:
        return jsonify({"error": str(e)}), 500, headers