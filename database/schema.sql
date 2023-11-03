--
-- PostgreSQL database dump
--

--
-- Name: api; Type: SCHEMA; Schema: -; Owner: ${ROOT_USER_NAME}
--

CREATE SCHEMA api;


ALTER SCHEMA api OWNER TO ${ROOT_USER_NAME};

--
-- Name: trigger_set_updated_at(); Type: FUNCTION; Schema: public; Owner: ${ROOT_USER_NAME}
--

CREATE FUNCTION public.trigger_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;


ALTER FUNCTION public.trigger_set_updated_at() OWNER TO ${ROOT_USER_NAME};

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: knack; Type: TABLE; Schema: api; Owner: ${ROOT_USER_NAME}
--

CREATE TABLE api.knack (
    record_id text NOT NULL,
    app_id text NOT NULL,
    container_id text NOT NULL,
    record json NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE api.knack OWNER TO ${ROOT_USER_NAME};

--
-- Name: knack_metadata; Type: TABLE; Schema: api; Owner: ${ROOT_USER_NAME}
--

CREATE TABLE api.knack_metadata (
    app_id text NOT NULL,
    metadata json NOT NULL
);


ALTER TABLE api.knack_metadata OWNER TO ${ROOT_USER_NAME};

--
-- Name: road_conditions; Type: TABLE; Schema: api; Owner: ${ROOT_USER_NAME}
--

CREATE TABLE api.road_conditions (
    voltage_y numeric,
    voltage_x numeric,
    voltage_ratio numeric,
    air_temp_secondary numeric,
    temp_surface numeric,
    condition_code_displayed numeric,
    condition_code_measured numeric,
    condition_text_displayed text,
    condition_text_measured text,
    friction_code_displayed numeric,
    friction_code_measured numeric,
    friction_value_displayed numeric,
    friction_value_measured numeric,
    dirty_lens_score numeric,
    grip_text text,
    relative_humidity numeric,
    air_temp_primary numeric,
    air_temp_tertiary numeric,
    status_code numeric,
    "timestamp" timestamp with time zone,
    sensor_id numeric NOT NULL,
    id integer NOT NULL
);


ALTER TABLE api.road_conditions OWNER TO ${ROOT_USER_NAME};

--
-- Name: road_conditions_id_seq; Type: SEQUENCE; Schema: api; Owner: ${ROOT_USER_NAME}
--

CREATE SEQUENCE api.road_conditions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE api.road_conditions_id_seq OWNER TO ${ROOT_USER_NAME};

--
-- Name: road_conditions_id_seq; Type: SEQUENCE OWNED BY; Schema: api; Owner: ${ROOT_USER_NAME}
--

ALTER SEQUENCE api.road_conditions_id_seq OWNED BY api.road_conditions.id;


--
-- Name: road_conditions id; Type: DEFAULT; Schema: api; Owner: ${ROOT_USER_NAME}
--

ALTER TABLE ONLY api.road_conditions ALTER COLUMN id SET DEFAULT nextval('api.road_conditions_id_seq'::regclass);


--
-- Name: knack_metadata knack_metadata_pkey; Type: CONSTRAINT; Schema: api; Owner: ${ROOT_USER_NAME}
--

ALTER TABLE ONLY api.knack_metadata
    ADD CONSTRAINT knack_metadata_pkey PRIMARY KEY (app_id);


--
-- Name: knack knack_pkey; Type: CONSTRAINT; Schema: api; Owner: ${ROOT_USER_NAME}
--

ALTER TABLE ONLY api.knack
    ADD CONSTRAINT knack_pkey PRIMARY KEY (record_id, app_id, container_id);


--
-- Name: road_conditions road_conditions_pkey; Type: CONSTRAINT; Schema: api; Owner: ${ROOT_USER_NAME}
--

ALTER TABLE ONLY api.road_conditions
    ADD CONSTRAINT road_conditions_pkey PRIMARY KEY (id);


--
-- Name: knack_container_id_idx; Type: INDEX; Schema: api; Owner: ${ROOT_USER_NAME}
--

CREATE INDEX knack_container_id_idx ON api.knack USING btree (container_id);


--
-- Name: road_conditions_timestamp_idx; Type: INDEX; Schema: api; Owner: ${ROOT_USER_NAME}
--

CREATE INDEX road_conditions_timestamp_idx ON api.road_conditions USING btree ("timestamp");


--
-- Name: knack set_updated_at; Type: TRIGGER; Schema: api; Owner: ${ROOT_USER_NAME}
--

CREATE TRIGGER set_updated_at BEFORE INSERT OR UPDATE ON api.knack FOR EACH ROW EXECUTE FUNCTION public.trigger_set_updated_at();


--
-- Name: SCHEMA api; Type: ACL; Schema: -; Owner: ${ROOT_USER_NAME}
--

GRANT USAGE ON SCHEMA api TO ${PRIVILEGED_USER_NAME};
GRANT USAGE ON SCHEMA api TO ${ANON_USER_NAME};


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: ${ROOT_USER_NAME}
--

REVOKE ALL ON SCHEMA public FROM rdsadmin;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO ${ROOT_USER_NAME};
GRANT ALL ON SCHEMA public TO PUBLIC;
GRANT USAGE ON SCHEMA public TO ${PRIVILEGED_USER_NAME};


--
-- Name: TABLE knack; Type: ACL; Schema: api; Owner: ${ROOT_USER_NAME}
--

GRANT ALL ON TABLE api.knack TO ${PRIVILEGED_USER_NAME};


--
-- Name: TABLE knack_metadata; Type: ACL; Schema: api; Owner: ${ROOT_USER_NAME}
--

GRANT ALL ON TABLE api.knack_metadata TO ${PRIVILEGED_USER_NAME};


--
-- Name: TABLE road_conditions; Type: ACL; Schema: api; Owner: ${ROOT_USER_NAME}
--

GRANT ALL ON TABLE api.road_conditions TO ${PRIVILEGED_USER_NAME};
GRANT SELECT ON TABLE api.road_conditions TO ${ANON_USER_NAME};


--
-- Name: SEQUENCE road_conditions_id_seq; Type: ACL; Schema: api; Owner: ${ROOT_USER_NAME}
--

GRANT SELECT,USAGE ON SEQUENCE api.road_conditions_id_seq TO ${PRIVILEGED_USER_NAME};
GRANT SELECT,USAGE ON SEQUENCE api.road_conditions_id_seq TO ${ANON_USER_NAME};


--
-- PostgreSQL database dump complete
--
