--
-- tables:
-- gateway_audit_trail_nullonlyft:
--     - null only api_audit_trail_id
--     - full text index on request_data
--     - query:
--          select requestid, request_data
--          from gateway_audit_trail_nullonlyft
--          where match(request_data)
--          against ("+204a0a4c+3491+4279+9843+43c30a in boolean mode);
--
-- gat_ids_username:
--     - join table that will be populated
--       by stored procedure
--
-- aat_username:
--      - 1 column table with distinct usernames
--
-- api_audit_trail:
--      - an exact copy of prod table
--      - add an index on username, though
--
-- And... go
--


use wfs_test;

--
-- create the working tables
--
-- set global innodb_file_format='Barracuda';
-- set global innodb_file_format_max='Barracuda';

-- create gateway_audit_trail_nullonlyft and add full text index
--
drop table if exists gateway_audit_trail_nullonlyft;
create table gateway_audit_trail_nullonlyft like gateway_audit_trail;
-- ~ 16 mins
insert into gateway_audit_trail_nullonlyft
    select * from gateway_audit_trail
    where request = 'GetAccountBalance'
    and api_audit_trail_id is NULL;
-- ~ 10 mins
create fulltext index idx_ft on gateway_audit_trail_nullonlyft(request_data);

-- username table
--
drop table if exists aat_username;
-- 30 sec
create table aat_username as
select
    distinct(username)
from
    api_audit_trail
where
    username is not null
    and username != '';
-- add index on
alter table aat_username add index idx_username (username);

-- join table that will be populated by stored procedure
--
drop table if exists gat_ids_username;
create table gat_ids_username (
  gat_id bigint(20) unsigned not null,
  aat_id bigint(20) unsigned default null,
  username varchar(45) default null,
  create_date datetime not null,
  last_modified_date datetime default null,
  primary key (gat_id),
  key idx_username (username),
  key idx_create_date (create_date),
  key idx_last_modified_date (last_modified_date)
) engine=innodb default charset=latin1;

-- log table
--
drop table if exists sp_log;
create table sp_log (
    code varchar(20) default '00000',
    msg varchar(100),
    username varchar(45)
);

-- Create stored procedure
--
drop procedure if exists wfs_unbork;

delimiter $$
create procedure wfs_unbork()
begin
    declare code varchar(20) default '00000';
    declare msg varchar(100);
    declare v_finished integer default 0;
    declare v_username varchar(45);
    declare cr_username cursor for
        select username from aat_username;
    declare continue handler for not found set v_finished = 1;
    -- declare continue handler for 1062
    --    select 'Error, duplicate key';
    declare continue handler for SQLEXCEPTION
        begin
            GET DIAGNOSTICS CONDITION 1
            code = RETURNED_SQLSTATE, msg = MESSAGE_TEXT;
        end;

    truncate gat_ids_username;
    truncate sp_log;
    open cr_username;
    get_username: loop
        fetch cr_username into v_username;
        if v_finished = 1 then leave get_username; end if;

        -- in ft search a '-' is OR and '+' is AND
        set @s_username = concat('"+',replace(v_username, '-', '+'),'"');
        set @ps_username = v_username;

        prepare stmt from
        'insert into gat_ids_username
            select id,null,?,create_date,last_modified_date
            from gateway_audit_trail_nullonlyft
            where match(request_data) against (? in boolean mode)';

        -- select @ps_username, @s_username, v_username;
        execute stmt using @ps_username, @s_username;
        if code != '00000' then
            insert into sp_log values (code, msg, @ps_username);
            -- select code, msg;
        end if;

        deallocate prepare stmt;

    end loop get_username;
    close cr_username;
    show errors;
    show warnings;
end$$
delimiter ;

-- should run for 1 hour
call wfs_unbork();

--
-- now get the aat IDs
--

-- need to add index on username
-- todo: get time estimate
alter table api_audit_trail add index idx_username (username);

-- expected time = 3.5 hours
update gat_ids_username giu
join
    (select
        aat.id aatId, giu.gat_id gatId
    from
        gat_ids_username giu
    join api_audit_trail aat on
        giu.username = aat.username
        and giu.create_date >= aat.create_date
        and giu.last_modified_date <= aat.last_modified_date
    ) as joinTable on giu.gat_id = joinTable.gatId
set
    giu.aat_id = joinTable.aatId;


--
-- the end
--


-- Can now send gat_ids_username to production
--
-- update
--     gateway_audit_trail gat
-- join
--     gat_ids_username giu on
--         giu.gat_id = gat.gat_id
-- set
--     gat.api_audit_trail_id = giu.aat_id;
