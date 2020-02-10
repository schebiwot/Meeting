-- auto-generated definition
create table room
(
    id          INTEGER      not null
        primary key,
    name        VARCHAR(100) not null,
    capacity    INTEGER      not null,
    location    VARCHAR(100),
    booked      BOOLEAN,
    time_booked DATETIME,
    check (booked IN (0, 1))
);

