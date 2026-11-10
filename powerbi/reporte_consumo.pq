// (Opcional) Resumen ya agregado por servicio, igual a la tabla del reporte web sin filtros.
let
    Fuente = Json.Document(Web.Contents(BaseUrl, [
        RelativePath = "api/reportes/consumo", Headers = [#"X-API-Key" = ApiKey]])),
    PorServicio = Table.FromRecords(Fuente[por_servicio])
in
    PorServicio
