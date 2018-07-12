-- Adminer 4.6.3-dev PostgreSQL dump

\connect "dt0gn6vd2eev9";

DROP TABLE IF EXISTS "checkins";
CREATE TABLE "public"."checkins" (
    "zipcode" character(5) NOT NULL,
    "username" character varying NOT NULL,
    "comment" character varying NOT NULL,
    "date" date NOT NULL,
    CONSTRAINT "checkins_username_fkey" FOREIGN KEY (username) REFERENCES users(username) NOT DEFERRABLE
) WITH (oids = false);


DROP TABLE IF EXISTS "locations";
CREATE TABLE "public"."locations" (
    "zipcode" character(5) NOT NULL,
    "city" character varying NOT NULL,
    "state" character(2) NOT NULL,
    "lat" numeric NOT NULL,
    "long" numeric NOT NULL,
    "pop" integer NOT NULL,
    CONSTRAINT "locations_pkey" PRIMARY KEY ("zipcode")
) WITH (oids = false);


DROP TABLE IF EXISTS "users";
DROP SEQUENCE IF EXISTS users_id_seq;
CREATE SEQUENCE users_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;

CREATE TABLE "public"."users" (
    "id" integer DEFAULT nextval('users_id_seq') NOT NULL,
    "username" character varying,
    "password" character varying,
    CONSTRAINT "users_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "users_username_key" UNIQUE ("username")
) WITH (oids = false);


-- 2018-07-12 21:17:32.35381+00