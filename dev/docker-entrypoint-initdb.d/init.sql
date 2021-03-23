--
-- PostgreSQL database dump
--

-- Dumped from database version 12.5
-- Dumped by pg_dump version 13.1 (Debian 13.1-1.pgdg100+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


-- custom role declarations no included in pg_dump
create role authenticator noinherit;
create role my_api_user nologin;
grant my_api_user to authenticator;

create role web_anon nologin;
grant web_anon to authenticator;

--
-- Name: api; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA api;


ALTER SCHEMA api OWNER TO postgres;

--
-- Name: trigger_set_updated_at(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trigger_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;


ALTER FUNCTION public.trigger_set_updated_at() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: knack; Type: TABLE; Schema: api; Owner: postgres
--

CREATE TABLE api.knack (
    record_id text NOT NULL,
    app_id text NOT NULL,
    container_id text NOT NULL,
    record json NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE api.knack OWNER TO postgres;

--
-- Name: knack_metadata; Type: TABLE; Schema: api; Owner: postgres
--

CREATE TABLE api.knack_metadata (
    app_id text NOT NULL,
    metadata json NOT NULL
);


ALTER TABLE api.knack_metadata OWNER TO postgres;

--
-- Name: knack_metadata knack_metadata_pkey; Type: CONSTRAINT; Schema: api; Owner: postgres
--

ALTER TABLE ONLY api.knack_metadata
    ADD CONSTRAINT knack_metadata_pkey PRIMARY KEY (app_id);


--
-- Name: knack knack_pkey; Type: CONSTRAINT; Schema: api; Owner: postgres
--

ALTER TABLE ONLY api.knack
    ADD CONSTRAINT knack_pkey PRIMARY KEY (record_id, app_id, container_id);


--
-- Name: knack_container_id_idx; Type: INDEX; Schema: api; Owner: postgres
--

CREATE INDEX knack_container_id_idx ON api.knack USING btree (container_id);


--
-- Name: knack set_updated_at; Type: TRIGGER; Schema: api; Owner: postgres
--

CREATE TRIGGER set_updated_at BEFORE INSERT OR UPDATE ON api.knack FOR EACH ROW EXECUTE FUNCTION public.trigger_set_updated_at();


--
-- Name: SCHEMA api; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA api TO my_api_user;
GRANT USAGE ON SCHEMA api TO web_anon;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;
GRANT USAGE ON SCHEMA public TO my_api_user;


--
-- Name: TABLE knack; Type: ACL; Schema: api; Owner: postgres
--

GRANT ALL ON TABLE api.knack TO my_api_user;


--
-- Name: TABLE knack_metadata; Type: ACL; Schema: api; Owner: postgres
--

GRANT ALL ON TABLE api.knack_metadata TO my_api_user;

--
-- PostgreSQL database dump complete
--
