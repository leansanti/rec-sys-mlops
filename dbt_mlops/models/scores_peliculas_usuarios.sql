
SELECT * FROM {{ ref('scores') }} sc 
INNER JOIN {{ ref('peliculas') }} using(movie_id)
INNER JOIN {{ ref('usuarios') }} using(user_id)