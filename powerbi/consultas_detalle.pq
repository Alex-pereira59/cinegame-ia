// Power BI Desktop → Obtener datos → Consulta en blanco → Editor avanzado → pegar.
// Cree antes dos parámetros (Inicio → Administrar parámetros):  BaseUrl (texto) y ApiKey (texto).
// Al pedir credenciales elija "Anónimo": la autenticación va en el header X-API-Key.
let
    Fuente = Json.Document(
        Web.Contents(BaseUrl, [
            RelativePath = "api/reportes/consultas-detalle",
            Headers = [#"X-API-Key" = ApiKey]
        ])
    ),
    Tabla = Table.FromRecords(Fuente),
    Tipos = Table.TransformColumnTypes(Tabla, {
        {"consulta_id", Int64.Type}, {"fecha", type date}, {"fecha_hora", type datetime},
        {"usuario", type text}, {"servicio", type text},
        {"tokens_entrada", Int64.Type}, {"tokens_salida", Int64.Type}, {"tokens_total", Int64.Type}
    }),
    NombreServicio = Table.AddColumn(Tipos, "servicio_nombre", each
        if [servicio] = "chat_rag" then "Chatbot del catálogo"
        else if [servicio] = "recomendador" then "Agente recomendador"
        else if [servicio] = "novedades" then "Agente de novedades"
        else [servicio], type text)
in
    NombreServicio
