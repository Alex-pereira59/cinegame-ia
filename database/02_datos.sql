-- CineGame AI - Datos iniciales para demostración
-- Contraseñas: admin / Admin123!   alex, maria / Usuario123!

INSERT INTO usuarios (username, nombre, email, password_hash, rol, activo, limite_tokens, creado_en) VALUES
('admin', 'Administrador', 'admin@example.com', '$2b$12$kOFKsFWCAnTUieVTN74HGOcAcGuyZnWfdAwQ4VWORjJZmL1KkFJ7S', 'admin', TRUE, 1000000, NOW()),
('alex', 'Alex de León', 'alex@example.com', '$2b$12$39kRap4D8EJd5PbmHsEW4.GAdsiXqHF8icl0dZh3lRNbtaN656Kha', 'usuario', TRUE, 50000, NOW()),
('maria', 'María López', 'maria@example.com', '$2b$12$0k.BFcqRQ0VOn.P2bUFf/ezuckTAhUf1m5q8d9w7oEcbIlvPQwnli', 'usuario', TRUE, 3000, NOW());

INSERT INTO servicios_ia (codigo, nombre, descripcion, activo, modelo, temperatura, max_pasos, prompt_sistema) VALUES
('chat_rag', 'Chatbot del catálogo (RAG)', 'Responde preguntas sobre películas y videojuegos usando únicamente el catálogo almacenado.', TRUE, NULL, 0.2, 1, 'Eres el asistente de CineGame AI, un catálogo de películas y videojuegos. Responde en español, de forma clara y breve, usando ÚNICAMENTE la información del CONTEXTO recuperado de la base de datos. Cita cada título que menciones con su identificador, por ejemplo [#12]. Si el contexto no contiene datos para responder, di exactamente: "No tengo información suficiente en el catálogo para responder esa pregunta." y sugiere cómo reformularla. No inventes títulos, calificaciones ni datos.'),
('recomendador', 'Agente recomendador', 'Busca candidatos según tus preferencias, consulta reseñas de la crítica, los compara y recomienda.', TRUE, NULL, 0.3, 6, 'Eres un agente recomendador de películas y videojuegos. Trabaja en varios pasos usando herramientas:
1) Identifica las preferencias del usuario (tipo, género, plataforma, calificación, gustos).
2) Busca candidatos con buscar_catalogo. Si hay pocos o ninguno, amplía los filtros y vuelve a buscar.
3) Para los 2 o 3 mejores candidatos consulta reseñas/recepción crítica con consultar_wikipedia (si no hay datos en español, intenta con idioma ''en'').
4) Compara los candidatos en una tabla Markdown (título, año, calificación del catálogo, puntos fuertes, puntos débiles según la crítica).
5) Da una recomendación final justificada.
Responde en español, cita los títulos del catálogo como [#id] y termina con una sección ''Fuentes'' con los enlaces consultados. No inventes datos que no hayas obtenido de las herramientas.'),
('novedades', 'Agente de novedades', 'Busca noticias recientes de un título o saga y amplía la búsqueda cuando falta información.', TRUE, NULL, 0.3, 6, 'Eres un agente de novedades de películas y videojuegos. Trabaja en varios pasos usando herramientas:
1) Identifica el título o saga solicitado.
2) Busca noticias recientes con buscar_noticias.
3) Si las noticias son pocas, antiguas o no responden la pregunta, AMPLÍA la búsqueda: usa el nombre de la saga o del estudio, busca en inglés (idioma ''en'') y/o consulta consultar_wikipedia para el contexto.
4) Revisa si el título existe en el catálogo propio con buscar_catalogo y menciónalo.
5) Redacta un resumen ordenado por fecha (lo más reciente primero) con viñetas.
Responde en español, indica las fechas y termina con una sección ''Fuentes'' con medio y enlace. Si no encuentras información fiable, dilo claramente.');

INSERT INTO titulos (tipo, titulo, genero, anio, calificacion, creador, plataforma, clasificacion, descripcion) VALUES
('pelicula', 'El Padrino', 'Drama, Crimen', 1972, 9.2, 'Francis Ford Coppola', NULL, 'R', 'El patriarca de una familia mafiosa de Nueva York transfiere el control del negocio a su hijo menor, que pasa de ser un outsider a un líder implacable.'),
('pelicula', 'Cadena perpetua', 'Drama', 1994, 9.3, 'Frank Darabont', NULL, 'R', 'Un banquero condenado injustamente forja una amistad duradera dentro de la prisión de Shawshank mientras planea en secreto su libertad.'),
('pelicula', 'Forrest Gump', 'Drama, Romance', 1994, 8.8, 'Robert Zemeckis', NULL, 'PG-13', 'Un hombre de gran corazón y pocas luces atraviesa sin proponérselo varios momentos clave de la historia de Estados Unidos.'),
('pelicula', 'Parásitos', 'Drama, Suspenso', 2019, 8.5, 'Bong Joon-ho', NULL, 'R', 'Una familia pobre se infiltra poco a poco en la vida de una familia adinerada hasta que un secreto en el sótano lo cambia todo.'),
('pelicula', 'Oppenheimer', 'Drama, Historia', 2023, 8.3, 'Christopher Nolan', NULL, 'R', 'Retrato del físico que dirigió el Proyecto Manhattan y de las consecuencias morales y políticas de la bomba atómica.'),
('pelicula', 'Coco', 'Animación, Aventura, Familiar', 2017, 8.4, 'Lee Unkrich', NULL, 'PG', 'Un niño mexicano que sueña con ser músico viaja a la Tierra de los Muertos durante el Día de Muertos para descubrir la historia de su familia.'),
('pelicula', 'El viaje de Chihiro', 'Animación, Fantasía, Aventura', 2001, 8.6, 'Hayao Miyazaki', NULL, 'PG', 'Una niña queda atrapada en un mundo de espíritus y debe trabajar en una casa de baños para liberar a sus padres convertidos en cerdos.'),
('pelicula', 'Indiana Jones y los cazadores del arca perdida', 'Aventura, Acción', 1981, 8.4, 'Steven Spielberg', NULL, 'PG', 'Un arqueólogo aventurero compite contra agentes nazis para encontrar el Arca de la Alianza.'),
('pelicula', 'Jurassic Park', 'Aventura, Ciencia ficción', 1993, 8.2, 'Steven Spielberg', NULL, 'PG-13', 'Un parque temático con dinosaurios clonados se sale de control durante una visita de inspección.'),
('pelicula', 'El Señor de los Anillos: La Comunidad del Anillo', 'Fantasía, Aventura', 2001, 8.9, 'Peter Jackson', NULL, 'PG-13', 'Un hobbit emprende un viaje junto a una comunidad de aliados para destruir un anillo de poder antes de que caiga en manos del Señor Oscuro.'),
('pelicula', 'Interestelar', 'Ciencia ficción, Drama', 2014, 8.7, 'Christopher Nolan', NULL, 'PG-13', 'Un grupo de astronautas viaja a través de un agujero de gusano buscando un nuevo hogar para la humanidad mientras la Tierra agoniza.'),
('pelicula', 'Matrix', 'Ciencia ficción, Acción', 1999, 8.7, 'Lana y Lilly Wachowski', NULL, 'R', 'Un programador descubre que la realidad es una simulación creada por máquinas y se une a la resistencia humana.'),
('pelicula', 'Dune: Parte Dos', 'Ciencia ficción, Aventura', 2024, 8.5, 'Denis Villeneuve', NULL, 'PG-13', 'Paul Atreides se une a los Fremen en el desierto de Arrakis para vengarse de quienes destruyeron a su familia.'),
('pelicula', 'Blade Runner 2049', 'Ciencia ficción, Drama', 2017, 8.0, 'Denis Villeneuve', NULL, 'R', 'Un replicante policía descubre un secreto que podría desestabilizar la sociedad y lo lleva a buscar a un antiguo blade runner.'),
('pelicula', 'Mad Max: Furia en el camino', 'Acción, Aventura', 2015, 8.1, 'George Miller', NULL, 'R', 'En un desierto postapocalíptico, una guerrera huye de un tirano junto a un grupo de prisioneras y un vagabundo llamado Max.'),
('pelicula', 'John Wick', 'Acción, Suspenso', 2014, 7.4, 'Chad Stahelski', NULL, 'R', 'Un asesino retirado vuelve a la acción para vengarse de los criminales que le arrebataron lo último que le quedaba.'),
('pelicula', 'Batman: El caballero de la noche', 'Acción, Crimen, Drama', 2008, 9.0, 'Christopher Nolan', NULL, 'PG-13', 'Batman enfrenta al Joker, un criminal que busca sumir a Ciudad Gótica en el caos y poner a prueba la moral de sus héroes.'),
('pelicula', 'El conjuro', 'Terror', 2013, 7.5, 'James Wan', NULL, 'R', 'Dos investigadores de fenómenos paranormales ayudan a una familia aterrorizada por una presencia oscura en su granja.'),
('pelicula', 'Hereditary', 'Terror, Drama', 2018, 7.3, 'Ari Aster', NULL, 'R', 'Tras la muerte de la abuela, una familia empieza a descubrir secretos perturbadores sobre sus antepasados.'),
('pelicula', '¡Huye!', 'Terror, Suspenso', 2017, 7.8, 'Jordan Peele', NULL, 'R', 'Un joven afroamericano visita a la familia de su novia blanca y descubre que esconden algo siniestro.'),
('pelicula', 'Superbad', 'Comedia', 2007, 7.6, 'Greg Mottola', NULL, 'R', 'Dos amigos inseparables intentan conseguir alcohol para una fiesta antes de separarse para ir a la universidad.'),
('pelicula', 'Toy Story', 'Animación, Comedia, Familiar', 1995, 8.3, 'John Lasseter', NULL, 'G', 'Los juguetes de un niño cobran vida cuando nadie los ve; un vaquero siente celos del nuevo astronauta favorito.'),
('pelicula', 'La La Land', 'Musical, Romance, Drama', 2016, 8.0, 'Damien Chazelle', NULL, 'PG-13', 'Una aspirante a actriz y un pianista de jazz se enamoran en Los Ángeles mientras persiguen sus sueños.'),
('pelicula', 'Spider-Man: Un nuevo universo', 'Animación, Acción, Aventura', 2018, 8.4, 'Bob Persichetti, Peter Ramsey, Rodney Rothman', NULL, 'PG', 'Miles Morales se convierte en Spider-Man y conoce a otras versiones del héroe provenientes de distintas dimensiones.'),
('videojuego', 'The Legend of Zelda: Breath of the Wild', 'Aventura, Mundo abierto', 2017, 9.7, 'Nintendo', 'Nintendo Switch, Wii U', 'E10+', 'Link despierta tras cien años y explora libremente un Hyrule en ruinas para derrotar a Ganon.'),
('videojuego', 'The Legend of Zelda: Tears of the Kingdom', 'Aventura, Mundo abierto', 2023, 9.6, 'Nintendo', 'Nintendo Switch', 'E10+', 'Secuela que añade islas en el cielo, profundidades subterráneas y habilidades para construir vehículos y artefactos.'),
('videojuego', 'Red Dead Redemption 2', 'Acción, Aventura, Mundo abierto', 2018, 9.7, 'Rockstar Games', 'PS4, Xbox One, PC', 'M', 'Arthur Morgan, miembro de una banda de forajidos, vive el ocaso del Lejano Oeste en una historia de lealtad y redención.'),
('videojuego', 'The Last of Us Parte I', 'Acción, Aventura, Supervivencia', 2022, 8.9, 'Naughty Dog', 'PS5, PC', 'M', 'Joel escolta a Ellie a través de un Estados Unidos devastado por una infección fúngica; remake del original de 2013.'),
('videojuego', 'God of War Ragnarök', 'Acción, Aventura', 2022, 9.4, 'Santa Monica Studio', 'PS4, PS5, PC', 'M', 'Kratos y su hijo Atreus recorren los nueve reinos mientras se acerca el fin del mundo nórdico.'),
('videojuego', 'Uncharted 4: El desenlace del ladrón', 'Acción, Aventura', 2016, 9.3, 'Naughty Dog', 'PS4, PS5, PC', 'T', 'Nathan Drake sale del retiro para ayudar a su hermano a encontrar el tesoro de un pirata legendario.'),
('videojuego', 'Elden Ring', 'RPG, Acción, Mundo abierto', 2022, 9.5, 'FromSoftware', 'PS4, PS5, Xbox, PC', 'M', 'Un Sinluz explora las Tierras Intermedias para convertirse en Señor del Círculo en un mundo creado junto a George R. R. Martin.'),
('videojuego', 'The Witcher 3: Wild Hunt', 'RPG, Mundo abierto', 2015, 9.3, 'CD Projekt Red', 'PS4, PS5, Xbox, Switch, PC', 'M', 'Geralt de Rivia busca a su hija adoptiva Ciri mientras la Cacería Salvaje la persigue.'),
('videojuego', 'Baldur''s Gate 3', 'RPG, Estrategia por turnos', 2023, 9.6, 'Larian Studios', 'PC, PS5, Xbox Series', 'M', 'Un grupo de aventureros infectados por un parásito mental debe encontrar una cura en un RPG basado en Dungeons & Dragons.'),
('videojuego', 'Final Fantasy VII Rebirth', 'RPG, Acción', 2024, 9.2, 'Square Enix', 'PS5, PC', 'T', 'Cloud y sus aliados salen de Midgar persiguiendo a Sefirot en la segunda parte del remake de Final Fantasy VII.'),
('videojuego', 'Persona 5 Royal', 'RPG, Simulación social', 2020, 9.5, 'Atlus', 'PS4, PS5, Switch, Xbox, PC', 'M', 'Estudiantes de Tokio llevan una doble vida como Ladrones Fantasma que cambian el corazón de adultos corruptos.'),
('videojuego', 'Halo Infinite', 'Disparos, Acción', 2021, 8.7, '343 Industries', 'Xbox Series, Xbox One, PC', 'T', 'El Jefe Maestro regresa para enfrentar a los Desterrados en el anillo Zeta Halo con una campaña semiabierta.'),
('videojuego', 'DOOM Eternal', 'Disparos, Acción', 2020, 8.9, 'id Software', 'PS4, Xbox One, Switch, PC', 'M', 'El Doom Slayer combate hordas demoníacas que han invadido la Tierra en un shooter de ritmo frenético.'),
('videojuego', 'Call of Duty: Modern Warfare II', 'Disparos, Acción', 2022, 7.5, 'Infinity Ward', 'PS4, PS5, Xbox, PC', 'M', 'La Fuerza Operativa 141 persigue una amenaza terrorista internacional; incluye modos multijugador competitivos.'),
('videojuego', 'Valorant', 'Disparos, Táctico, Multijugador', 2020, 8.0, 'Riot Games', 'PC, PS5, Xbox Series', 'T', 'Shooter táctico 5 contra 5 donde cada agente tiene habilidades únicas que complementan el juego de armas.'),
('videojuego', 'Resident Evil 4 (Remake)', 'Terror, Supervivencia, Acción', 2023, 9.3, 'Capcom', 'PS4, PS5, Xbox Series, PC', 'M', 'Leon S. Kennedy viaja a una aldea europea para rescatar a la hija del presidente, secuestrada por un culto.'),
('videojuego', 'Silent Hill 2 (Remake)', 'Terror, Supervivencia', 2024, 8.6, 'Bloober Team', 'PS5, PC', 'M', 'James Sunderland llega a Silent Hill tras recibir una carta de su esposa fallecida.'),
('videojuego', 'Hollow Knight', 'Metroidvania, Acción, Plataformas', 2017, 9.0, 'Team Cherry', 'PC, Switch, PS4, Xbox One', 'E10+', 'Un pequeño caballero explora el reino subterráneo en ruinas de Hallownest lleno de insectos y secretos.'),
('videojuego', 'Super Mario Bros. Wonder', 'Plataformas, Familiar', 2023, 9.2, 'Nintendo', 'Nintendo Switch', 'E', 'Mario y sus amigos viajan al Reino Flor, donde las Flores Maravilla transforman los niveles de formas sorprendentes.'),
('videojuego', 'Minecraft', 'Sandbox, Supervivencia, Familiar', 2011, 9.0, 'Mojang Studios', 'Multiplataforma', 'E10+', 'Mundo de bloques generado al azar donde se construye, se explora y se sobrevive, solo o con amigos.'),
('videojuego', 'Stardew Valley', 'Simulación, RPG, Familiar', 2016, 8.9, 'ConcernedApe', 'Multiplataforma', 'E10+', 'Heredas la granja de tu abuelo y reconstruyes tu vida cultivando, pescando y haciendo amigos en un pueblo.'),
('videojuego', 'EA Sports FC 25', 'Deportes, Fútbol', 2024, 7.4, 'EA Sports', 'PS4, PS5, Xbox, Switch, PC', 'E', 'Simulador de fútbol con licencias de clubes y ligas, modo carrera y el modo Ultimate Team.'),
('videojuego', 'Gran Turismo 7', 'Carreras, Simulación', 2022, 8.7, 'Polyphony Digital', 'PS4, PS5', 'E', 'Simulador de conducción con cientos de autos detallados, circuitos reales y un modo de colección de vehículos.'),
('videojuego', 'Forza Horizon 5', 'Carreras, Mundo abierto', 2021, 9.2, 'Playground Games', 'Xbox, PC, PS5', 'E', 'Festival de carreras en un mundo abierto inspirado en los paisajes de México.'),
('videojuego', 'Hades', 'Roguelike, Acción', 2020, 9.3, 'Supergiant Games', 'Multiplataforma', 'T', 'Zagreo, hijo de Hades, intenta escapar del inframundo con ayuda de los dioses del Olimpo; cada intento es distinto.');
