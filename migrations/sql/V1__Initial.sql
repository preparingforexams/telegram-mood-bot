create table users(
    id bigint primary key,
    first_name text not null
);

create table users_groups(
    user_id bigint not null references users(id),
    group_id bigint not null,
    primary key (user_id, group_id)
);

create table polls(
    id text primary key,
    group_id bigint not null,
    message_id bigint not null,
    creation_time timestamptz not null,
    close_time timestamptz
);

create index on polls(creation_time asc);
create index on polls(close_time asc);

create table poll_answers(
    user_id bigint not null references users(id),
    poll_id text not null references polls(id),
    time timestamptz not null,
    option integer,
    primary key (user_id, poll_id)
)
