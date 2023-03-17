@app.route("/query", methods=["POST"])
def query_database():
    nl_query = request.json.get("query", "")

    if not nl_query:
        return jsonify({"error": "No query provided"}), 400

    prompt = f"Translate the following English query into SQL: {nl_query}"

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )

    sql_query = response.choices[0].text.strip()
    try:
        result = datalake.query(sql_query)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
