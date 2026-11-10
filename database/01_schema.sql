-- CineGame AI - Script de creación de la base de datos (PostgreSQL)
-- Ejecutar sobre una base vacía: psql "$DATABASE_URL" -f 01_schema.sql

DROP TABLE IF EXISTS consultas, conversaciones, titulos, servicios_ia, usuarios CASCADE;

CREATE TABLE servicios_ia (
	id SERIAL NOT NULL, 
	codigo VARCHAR(50) NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	descripcion TEXT NOT NULL, 
	activo BOOLEAN NOT NULL, 
	modelo VARCHAR(100), 
	temperatura FLOAT NOT NULL, 
	max_pasos INTEGER NOT NULL, 
	prompt_sistema TEXT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo)
);


CREATE TABLE titulos (
	id SERIAL NOT NULL, 
	tipo VARCHAR(20) NOT NULL, 
	titulo VARCHAR(200) NOT NULL, 
	genero VARCHAR(100) NOT NULL, 
	anio INTEGER NOT NULL, 
	calificacion FLOAT NOT NULL, 
	creador VARCHAR(150) NOT NULL, 
	plataforma VARCHAR(150), 
	clasificacion VARCHAR(20), 
	descripcion TEXT NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_titulos_tipo ON titulos (tipo);

CREATE TABLE usuarios (
	id SERIAL NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	nombre VARCHAR(120) NOT NULL, 
	email VARCHAR(150), 
	password_hash VARCHAR(200) NOT NULL, 
	rol VARCHAR(20) NOT NULL, 
	activo BOOLEAN NOT NULL, 
	limite_tokens INTEGER NOT NULL, 
	api_key VARCHAR(80), 
	creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (api_key)
);

CREATE UNIQUE INDEX ix_usuarios_username ON usuarios (username);

CREATE TABLE conversaciones (
	id SERIAL NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	servicio VARCHAR(50) NOT NULL, 
	titulo VARCHAR(200) NOT NULL, 
	creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX ix_conversaciones_usuario_id ON conversaciones (usuario_id);

CREATE TABLE consultas (
	id SERIAL NOT NULL, 
	conversacion_id INTEGER, 
	usuario_id INTEGER NOT NULL, 
	servicio VARCHAR(50) NOT NULL, 
	pregunta TEXT NOT NULL, 
	respuesta TEXT NOT NULL, 
	fuentes TEXT NOT NULL, 
	pasos TEXT NOT NULL, 
	tokens_entrada INTEGER NOT NULL, 
	tokens_salida INTEGER NOT NULL, 
	tokens_total INTEGER NOT NULL, 
	creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversacion_id) REFERENCES conversaciones (id) ON DELETE CASCADE, 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX ix_consultas_servicio ON consultas (servicio);
CREATE INDEX ix_consultas_conversacion_id ON consultas (conversacion_id);
CREATE INDEX ix_consultas_creado_en ON consultas (creado_en);
CREATE INDEX ix_consultas_usuario_id ON consultas (usuario_id);

-- Vista de apoyo para reportes (consumo por día, usuario y servicio)
CREATE OR REPLACE VIEW v_consumo_diario AS
SELECT DATE(c.creado_en) AS fecha, u.username AS usuario, c.servicio,
       COUNT(*) AS consultas, SUM(c.tokens_entrada) AS tokens_entrada,
       SUM(c.tokens_salida) AS tokens_salida, SUM(c.tokens_total) AS tokens_total
FROM consultas c JOIN usuarios u ON u.id = c.usuario_id
GROUP BY DATE(c.creado_en), u.username, c.servicio;
