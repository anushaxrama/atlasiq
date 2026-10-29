select 'join_fanout' as failure
where (select count(*) from {{ref('fct_trips')}}) <> (select count(*) from {{source('raw','trips')}})
