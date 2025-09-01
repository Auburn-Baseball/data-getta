-- Delete all teams that have a conference of 'NotSet'
delete from teams t2 where t2."TeamName" in (select t."TeamName" from teams t where t."Conference" = 'NotSet');
