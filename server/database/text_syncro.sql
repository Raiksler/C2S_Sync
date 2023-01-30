--
-- PostgreSQL database dump
--

-- Dumped from database version 14.6 (Ubuntu 14.6-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.6 (Ubuntu 14.6-0ubuntu0.22.04.1)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: changelog; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.changelog (
    id bigint NOT NULL,
    base_hash character varying(255),
    new_line boolean,
    changes character varying(3000)
);


ALTER TABLE public.changelog OWNER TO postgres;

--
-- Name: changelog_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.changelog ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.changelog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Data for Name: changelog; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.changelog (id, base_hash, new_line, changes) FROM stdin;
\.


--
-- Name: changelog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.changelog_id_seq', 174, true);


--
-- Name: changelog changelog_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.changelog
    ADD CONSTRAINT changelog_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

