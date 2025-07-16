--
-- PostgreSQL database dump
--

-- Dumped from database version 10.23
-- Dumped by pg_dump version 10.23

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

--
-- Data for Name: enriched_circuits; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.enriched_circuits (id, network_name, device_tags, wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed, wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed, last_updated, created_at, pushed_to_meraki, pushed_date, wan1_ip, wan2_ip, wan1_arin_org, wan2_arin_org) FROM stdin;
25080	AZP 16	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-09 06:47:58.074315	\N	\N	\N	\N
25149	CAL 08	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25163	CAL 23	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25170	CAL 35	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25174	CAL 41	\N	AT&T Broadband II	940.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25176	CAL 43	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25177	CAL 44	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25150	CAL 09	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Frontier Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25161	CAL 21	\N	AT&T Broadband	45.0M x 6.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25162	CAL 22	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25071	AZP 03	\N	Cox Business BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:51:33.065235	2025-07-07 09:50:02.79366	t	2025-07-07 11:51:33.065235	\N	\N	\N	\N
25164	CAL 24	\N	Frontier Fios	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25179	CAL 47	\N	EB2-Frontier Fiber\t	500.0M x 500.0M	Primary	t	One Ring Networks	300.0M x 30.0M	Secondary	t	2025-07-07 16:41:34.319346	2025-07-07 09:50:02.79366	t	2025-07-07 16:41:34.319346	\N	\N	\N	\N
25067	AZN 05	\N	TransWorld	500.0M x 500.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25165	CAL 26	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25166	CAL 28	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25182	CAL 50	\N	Spectrum	500.0M x 500.0M	Primary	t	EB2-Frontier Fiber	600.0M x 35.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25168	CAL 31	\N	Spectrum	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25154	CAL 13	\N	Frontier Communications	1000.0M x 1000.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25178	CAL 46	\N	EB2-Frontier Fiber	500.0M x 500.0M	Primary	t	Accelerated Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25141	CAL_00	\N	Frontier Communications	500.0M x 500.0M	Primary	t	Charter Communications	600.0M x 35.0M	Secondary	t	2025-07-09 06:51:32.39197	2025-07-07 09:50:02.79366	t	2025-07-09 06:51:32.39197	\N	\N	\N	\N
25171	CAL 37	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25214	CAN 35	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast	300.0M x 35.0M	Secondary	t	2025-07-09 11:45:52.861169	2025-07-07 09:50:02.79366	t	2025-07-09 11:45:52.861169	\N	\N	\N	\N
25172	CAL 38	\N	Spectrum	300.0M x 20.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:23:03.149135	\N	\N	\N	\N
25205	CAN 25	\N	Comcast	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-09 15:02:27.953284	2025-07-07 09:50:02.79366	t	2025-07-09 15:02:27.953284	\N	\N	\N	\N
25175	CAL 42	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25042	ALN 01	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25049	ARL 04	\N	Altice West	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-08 10:07:11.163559	\N	\N	\N	\N
25072	AZP 05	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25180	CAL 48	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
27656	AL-HUB	{Hub}			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25143	CAL 02	\N	Spectrum	600.0M x 35.0M	Primary	t	Frontier MetroFiber	100.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25110	AZP 47	\N	Cox Business/BOI	300.0M x 50.0M	Primary	t	CenturyLink	10.0M x 1.0M	Secondary	t	2025-07-10 19:26:22.941547	2025-07-07 09:50:02.79366	t	2025-07-10 19:26:22.941547	\N	\N	\N	\N
27696	AZPB 20	{Lab}	Connected to Desert Ridge MX250		Primary	f	Digi	Cell	Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
27711	AZSB 01	{Lab}			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25184	CAN_00	\N	Comcast	\N	Primary	t	AT&T	\N	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25531	INI_00	\N	DSR Cincinnati Bell ADSL	400.0M x 200.0M	Primary	t	Charter Communications	\N	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25553	KSK_00	\N	Charter Communications	\N	Primary	t	AT&T	\N	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25749	NMA_00	\N	Comcast	\N	Primary	t	CenturyLink	\N	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25167	CAL 29	\N	Frontier	500.0M x 500.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 09:14:17.207359	2025-07-07 09:50:02.79366	t	2025-07-10 09:14:17.207359	\N	\N	\N	\N
25045	ALS 02	\N	C Spire	1000.0M x 1000.0M	Primary	t	Brightspeed	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25048	ARL 03	\N	Conway Corporation	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25074	AZP 08	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25079	AZP 14	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25087	AZP 23	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25095	AZP 31	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25099	AZP 35	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25101	AZP 37	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	CenturyLink/Qwest 	60.0M x 5.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25106	AZP 43	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	CenturyLink 	80.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25124	AZP 62	\N	Cox Business/BOI 	300.0M x 30.0M	Primary	f	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25129	AZT 02	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25134	AZT 10	\N	Cox Business/BOI	300.0M x 30.0M	Primary	f	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25136	AZT 12	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Lumen Qwest	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25924	TNN_00	\N	AT&T	\N	Primary	t	Comcast	\N	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26081	TXH_00	\N	AT&T	\N	Primary	t	Comcast	\N	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25145	CAL 04	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25477	ILC 01	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast	300.0M x 35.0M	Secondary	t	2025-07-09 15:05:44.746984	2025-07-07 09:50:02.79366	t	2025-07-09 15:05:44.746984	\N	\N	\N	\N
25219	CAN 40	\N	VZW Cell	Cell	Primary	t	Starlink	Satellite	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25480	ILC 04	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-09 15:08:25.816794	2025-07-07 09:50:02.79366	t	2025-07-09 15:08:25.816794	\N	\N	\N	\N
25247	CAS 02	\N	AT&T	Cell	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 13:30:37.325094	2025-07-07 09:50:02.79366	t	2025-07-10 13:30:37.325094	\N	\N	\N	\N
25043	ALN 02	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	Comcast Workplace	250.0M x 25.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25044	ALS 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Comcast Workplace	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25050	ARL 05	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Ritter Communications	250.0M x 250.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25054	ARO 03	\N	AT&T Broadband II	500.0M x 100.0M	Primary	t	Cox Business/BOI	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25055	ARO 04	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25098	AZP 34	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25120	AZP 58	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25121	AZP 59	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25127	AZS 01	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25135	AZT 11	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25146	CAL 05	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
27798	EQX-OOB-WA-01	{Hub}			Primary	f	Unknown		Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25157	CAL 17	\N	Frontier	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-09 06:50:17.970666	\N	\N	\N	\N
25160	CAL 20	\N	Frontier	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-09 06:50:41.633674	\N	\N	\N	\N
26165	TXHT00	\N	Comcast	\N	Primary	t	Unknown		Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25100	AZP 36	\N	Wyyerd Fiber	2000.0M x 2000.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25122	AZP 60	\N	Mediacom Communications Corporation	1000.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25051	ARL 06	\N	Brightspeed	300.0M x 30.0M	Primary	t	Altice West	100.0M x 100.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25052	ARO 01	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25065	AZN 03	\N	Sparklight	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-08 13:30:52.546181	2025-07-07 09:50:02.79366	t	2025-07-08 13:30:52.546181	\N	\N	\N	\N
25501	ILC 29	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast	300.0M x 35.0M	Secondary	t	2025-07-09 15:36:59.708172	2025-07-07 09:50:02.79366	t	2025-07-09 15:36:59.708172	\N	\N	\N	\N
25039	ALM 02	\N	Spectrum	300.0M x 20.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25075	AZP 09	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Lumen DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25082	AZP 18	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-CenturyLink DSL	80.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25090	AZP 26	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25091	AZP 27	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	CenturyLink/Qwest	40.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25092	AZP 28	\N	Cox Business/BOI	500.0M x 50.0M	Primary	t	CenturyLink/Qwest	140.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25093	AZP 29	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Lumen DSL	140.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25094	AZP 30	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25116	AZP 54	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	CenturyLink/Qwest	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25137	AZT 13	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	GTT ESA2 ADSL	12.0M x 1.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25148	CAL 07	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25245	CAS_00	\N	AT&T	\N	Primary	t	Cox Communications	\N	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
27848	Igor Lab	{Lab}	Unknown		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
27849	BSM Test Network	{Lab}	BSM Lab in the Test Lab area of Scottsdale HQ		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
27893	NEO 03 TEMP	{Lab}			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25224	CAN 45	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25225	CAN 46	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25183	CAL W01	\N	Frontier Fiber	1000.0M x 1000.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-09 06:51:11.440971	2025-07-07 09:50:02.79366	t	2025-07-09 06:51:11.440971	\N	\N	\N	\N
25229	CAN 50	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25230	CAN 51	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25234	CAN 55	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Succeed-net	100.0M x 7.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25038	ALM 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25041	ALM 04	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25046	ARL 01	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast Workplace	1000.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25056	ARO 05	\N	Yelcot Communications	300.0M x 30.0M	Primary	t	Ritter Communications	250.0M x 250.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25086	AZP 22	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25142	CAL 01	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Frontier Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25181	CAL 49	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25188	CAN 05	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25191	CAN 11	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25193	CAN 13	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25197	CAN 17	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband	45.0M x 6.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25199	CAN 19	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25201	CAN 21	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25202	CAN 22	\N	Comcast Workplace	15.0M x 15.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25209	CAN 30	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast	300.0 M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
27944	Central Store Test	{Lab}	Unknown		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
27947	DR VTV Test Lab II	{Lab}	Unknown		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
27949	EQX-DataCenter-WA	{Hub}	Unknown		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
27951	EQX-OOB-WA-02	{Hub}	Unknown		Primary	f	Unknown		Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
27952	East Store Test	{Lab}	Unknown		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25213	CAN 34	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25217	CAN 38	\N	AT&T Broadband II	2000.0M x 2000.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:29:56.934651	\N	\N	\N	\N
25218	CAN 39	\N	Astound	1000.0M x 20.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25220	CAN 41	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25221	CAN 42	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25222	CAN 43	\N	AT&T Broadband II	300.0M x 75.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25223	CAN 44	\N	Comcast Workplace	200.0M x 20.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25235	CAN 56	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25238	CAN 60	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Comcast Workplace	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25252	CAS 07	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	Cox Business/BOI	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25255	CAS 10	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Cox Business/BOI	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25273	CAS 31	\N	Frontier Fios	500.0M x 500.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25204	CAN 24	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25203	CAN 23	\N	AT&T Enterprises, LLC	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25363	FLJ_00	\N	Comcast	300.0M x 30.0M	Primary	t	AT&T	300.0M x 300.0M	Secondary	t	2025-07-09 15:05:14.37083	2025-07-07 09:50:02.79366	t	2025-07-09 15:05:14.37083	\N	\N	\N	\N
25102	AZP 38	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25105	AZP 42	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25111	AZP 48	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25112	AZP 49	\N	CenturyLink/Qwest	12.0M x 2.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25114	AZP 51	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25117	AZP 55	\N	CenturyLink Fiber Plus	500.0M x 500.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25266	CAS 21	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:31:00.460228	\N	\N	\N	\N
25281	CAS 39	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25285	CAS 43	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25293	CAS 51	\N	Cox Business/BOI 	300.0M x 30.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25294	CAS 53	\N	AT&T Broadband II	2000.0M x 2000.0M	Primary	t	Cox Business/BOI	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25295	COB 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25329	COD 36	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	CenturyLink	50.0 M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25336	COG 01	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Centurylink DSL	80.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25337	Cog 02	\N	Comcast	\N	Primary	t	Community Broadband Network	100.0 M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25342	COP 03	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25345	COS 03	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25355	FLD 01	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25357	FLD 04	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25361	FLG 03	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast Workplace	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25364	FLJ 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25365	FLJ 02	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25367	FLJ 05	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25369	FLJ 07	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25371	FLJ 10	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25373	FLJ 12	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast Workplace	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25374	FLM 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25375	FLM 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25379	FLO 04	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
28000	FP-iSeries-ATL	{Hub}	Unknown		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
28001	FP-iSeries-DAL	{Hub}	Unknown		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
28004	Flight Department - Pilot	{Lab}	Cox Communications		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25381	FLO 06	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25387	FLO 12	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25258	CAS 13	\N	Cox Business/BOI	300.0M x 30.0M	Primary	f	AT&T Broadband II	1000.0M x 1000.0M	Secondary	f	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25368	FLJ 06	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25057	ARO 06	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Cox Business/BOI	300.0M x 50.0M	Secondary	t	2025-07-08 10:22:42.338218	2025-07-07 09:50:02.79366	t	2025-07-08 10:22:42.338218	\N	\N	\N	\N
25402	FP-ATL-OOBMGMT-01	\N			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25083	AZP 19	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25085	AZP 21	\N	Cox Business/BOI	100.0M x 20.0M	Primary	t	CenturyLink/Embarq	80.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 14:15:13.168866	\N	\N	\N	\N
25097	AZP 33	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25128	AZT 01	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25389	FLO 14	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25390	FLO 15	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25392	FLP 01	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25395	FLP 04	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25396	FLS 01	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25398	FLS 03	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25399	FLS 04	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast Workplace	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25409	GAA 06	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25413	GAA 11	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25418	GAA 17	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25423	GAA 24	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25425	GAA 26	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25428	GAA 29	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast Workplace	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25431	GAA 32	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25437	GAA 38	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Hargray Cable	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25438	GAA 39	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25443	GAA 44	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	EB2-Windstream Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25446	GAACALLCNTR	\N	AT&T	\N	Primary	t	Charter Communications	\N	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25448	GAE 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Hargray Cable	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
27959	HQ-HUB	{Hub}			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25449	GAE 02	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25450	GAE 03	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25454	IAC 01	\N	Mediacom Communications Corporation	1000.0M x 30.0M	Primary	t	EB2-Lumen DSL	140.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25455	IAC 02	\N	Mediacom Communications Corporation	1000.0M x 30.0M	Primary	t	ImOn Communications	100.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25456	IAD 01	\N	Mediacom Communications Corporation	1000.0M x 30.0M	Primary	t	Metronet	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25460	IAD 05	\N	Mediacom/BOI	1000.0M x 30.0M	Primary	t	Metronet	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25464	IAN 02	\N	Mediacom Communications Corporation	1000.0M x 30.0M	Primary	t	Century Link/Qwest	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25469	IDB 01	\N	Cable One 	300.0M x 50.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25470	IDB 03	\N	EB2-CableOne Cable	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25472	IDB 05	\N	EB2-CableOne Cable	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25474	IDB 07	\N	EB2-CableOne Cable	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	80.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25475	IDN 01	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Ziply Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25481	ILC 05	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25484	ILC 08	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25126	AZP 64	\N	Starlink	Satellite	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25062	AZK 01	\N	Frontier	\N	Primary	t	Allo Communications	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-07 11:50:18.573974	\N	\N	\N	\N
25133	AZT 09	\N	Comcast Workplace	600.0M x 35.0M	Primary	f	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25212	CAN 33	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25226	CAN 47	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25227	CAN 48	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25476	ILC_00	\N	Comcast	\N	Primary	t	AT&T	\N	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25489	ILC 14	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25495	ILC 21	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Comcast Workplace	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25498	ILC 25	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25499	ILC 27	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25502	ILC 30	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25504	ILC 32	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25506	ILC 34	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	Comcast Workplace	200.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25507	ILC 35	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25508	ILC 36	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25509	ILC 37	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25521	ILW 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25525	INE 01	\N	Astound	500.0M x 20.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25526	INE 02	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25538	INI 08	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25541	INI 12	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25542	INI 13	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25544	INI 15	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25545	INI 16	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25547	INJ 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25549	INN 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25552	INW 03	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25555	KSK 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25558	KSK 05	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25560	KSL 01	\N	Midcontinent	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25561	KSM 01	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25562	KSM 02	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25563	KST 01	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Cox Business/BOI	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25565	KSW 02	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25567	KYB 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25570	KYL 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25571	KYL 03	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25572	LAS 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25573	LAS 02	\N	Altice West	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25575	MIA 01	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25118	AZP 56	\N	ComcastAgg	10.0M x 10.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-09 06:49:41.369535	2025-07-07 09:50:02.79366	t	2025-07-09 06:49:41.369535	\N	\N	\N	\N
25108	AZP 45	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25185	CAN 02	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:28:21.719328	\N	\N	\N	\N
25187	CAN 04	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	Accelerated	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25576	MIA 04	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25577	MIA 16	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25582	MID 04	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25584	MID 06	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25587	MID 10	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25588	MID 11	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25589	MID 12	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25597	MID 22	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25601	MID 26	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25602	MID 27	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25606	MIF 25	\N	Spectrum	940.0M x 35.0M	Primary	t	Comcast Workplace	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25609	MIG 08	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25610	MIG 09	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25611	MIG 23	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Frontier Fiber	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25612	MIG 24	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25614	MIG 29	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25615	MIG 30	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25616	MIH 27	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25617	MIK 06	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25618	MIK 14	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25619	MIK 30	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25620	MIK 31	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25621	MIL 00	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25625	MIM 01	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25628	MIS 12	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25629	MIS 17	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25630	MIS 20	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25654	MNM 22	\N	Spectrum	940.0M x 35.0M	Primary	t	EB2-Centurylink DSL	140.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25655	MNM 23	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Centurylink DSL	140.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25659	MNM 27	\N	CenturyLink Fiber Plus	500.0M x 500.0M	Primary	t	CTC	250.0M x 250.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25664	MOK 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25665	MOK 03	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25666	MOK 05	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25667	MOK 06	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25669	MON 01	\N	Altice West	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25671	MOO 02	\N	Mediacom Communications Corporation	1000.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25672	MOO 03	\N	Mediacom Communications Corporation	1000.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25674	MOR 01	\N	Fidelity Communications	350.0M x 20.0M	Primary	t	EB2-Sparklight Cable	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25678	MOS 03	\N	Spectrum	300.0M x 20.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25189	CAN 07	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25192	CAN 12	\N	Etheric Networks	10.0M x 10.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25195	CAN 15	\N	AT&T Broadband II	300.0M x 75.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25198	CAN 18	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25200	CAN 20	\N	Consolidated Communications	300.0M x 300.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25679	MOS 04	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25680	MOS 05	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25683	MOS 08	\N	Spectrum	600.0M x 35.0M	Primary	t	Brightspeed	100.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25689	MSN 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25690	MSN 02	\N	C Spire	300.0M x 300.0M	Primary	t	Comcast Workplace	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25695	NCC 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25696	NCC 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25698	NCC 04	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25699	NCC 05	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25700	NCC 06	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25701	NCC 07	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
28221	Temp Wireless	{Lab}			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25703	NCC 09	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25704	NCC 10	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25706	NCC 13	\N	Spectrum	600.0M x 35.0M	Primary	t	Lumos Networks	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25709	NCC 16	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25710	NCC 17	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25715	NCC 23	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25716	NCC 24	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25717	NCC 25	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25718	NCC 26	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	AT&T Broadband II	1000.0 M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25722	NCC 33	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25723	NCC 35	\N	Metronet	500.0M x 50.0M	Primary	t	Metronet	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25724	NCC 36	\N	Spectrum	600.0M x 35.0M	Primary	t	GreenLight	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25725	NCC 37	\N	Spectrum	600.0M x 35.0M	Primary	t	MetroNet	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25727	NCC 39	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25728	NCC 40	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Windstream Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25729	NCC 41	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25730	NCC 42	\N	AT&T Broadband II	100.0M x 20.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25735	NCC 47	\N	Spectrum	600.0M x 35.0M	Primary	t	MetroNet	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25738	NCC 52	\N	Spectrum	600.0M x 35.0M	Primary	t	Metronet	100.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25739	NCN 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Brightspeed	100.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25746	NEO 05	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25747	NEO 06	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25751	NMA 02	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	ComcastAgg CLink	20.0 M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25753	NMA 04	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Unite Private Networks	100.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25758	NMA 09	\N	SparkLight	300.0M x 30.0M	Primary	t	Comcast Workplace	200.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25766	NMF 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25770	NMS 02	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	CenturyLink	60.0M x 5.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25778	NVL 08	\N	CenturyLink Fiber Plus	500.0M x 500.0M	Primary	t	Cox Business/BOI	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25793	NVR 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25794	NVR 04	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25818	OHC 03	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25284	CAS 42	\N	Cox Communications		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25196	CAN 16	\N	Frontier	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-07 11:07:02.889081	\N	\N	\N	\N
25206	CAN 26	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25236	CAN 57	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25241	CAO 01	\N	AT&T	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25243	CAO 05	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25634	MNM 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25638	MNM 06	\N	Comcast Workplace	600.0M x 35.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25639	MNM 07	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25640	MNM 08	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	EB2-Centurylink DSL	140.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25642	MNM 10	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25645	MNM 13	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Lumen DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25647	MNM 15	\N	Spectrum	600.0M x 35.0M	Primary	t	Metronet	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25822	OHC 07	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25824	OHC 10	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25825	OHD 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25827	OHD 04	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25828	OHL 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Telephone Service Company TSC	200.0M x 50.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25829	OHN 01	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Windstream Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25830	OHN 02	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Cox Business/BOI	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25833	OHN 05	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25837	OHS 03	\N	Spectrum	600.0M x 35.0M	Primary	t	Altafiber	400.0M x 200.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25838	OHS 04	\N	Spectrum	600.0M x 35.0M	Primary	t	Altafiber	400.0M x 200.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25839	OHS 05	\N	Spectrum	600.0M x 35.0M	Primary	t	Altafiber	400.0M x 200.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25840	OHT 01	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	Buckeye Broadband Business	400.0M x 400.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25841	OHT 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
28316	Mt. Prospect Voice	{Voice}	AT&T BVOIP Asset ID IZEC561522ATI		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25842	OKA 01	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25845	OKO 02	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25846	OKO 03	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25848	OKO 05	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25850	OKO 07	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Cox Business/BOI	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25851	OKO 08	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25852	OKO 09	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25853	OKO 10	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25854	OKO 11	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	1000.0M x 200.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25644	MNM 12	\N	Metronet	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25421	GAA 21	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast Cable Communications, LLC	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25246	CAS 01	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25254	CAS 09	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25351	COW 02	\N	Elevate Internet	1000.0M x 1000.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:32:01.618273	\N	\N	\N	\N
25422	GAA 22	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25693	MTM 02	\N	Spectrum	600.0M x 35.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25702	NCC 08	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25858	OKO 15	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Cox Business/BOI	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25859	OKT 01	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Windstream Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25862	OKT 05	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	BTC Broadband	300.0M x 50.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25867	ORM 02	\N	Spectrum	600.0M x 35.0M	Primary	t	Hunter Communications	300.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25889	SCA 01	\N	Breezeline Formerly Atlantic Broadband	500.0M x 40.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25890	SCC 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25893	SCC 04	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25894	SCC 05	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25895	SCC 06	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25896	SCC 07	\N	Spectrum	600.0M x 35.0M	Primary	t	Comporium Com DIA	400.0M x 400.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25897	SCC 08	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Windstream Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25898	SCC 09	\N	Spectrum	600.0M x 35.0M	Primary	t	Comporium Com	400.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25899	SCC 10	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25900	SCC 11	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25901	SCC 12	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25905	SCC 16	\N	Spectrum	600.0M x 35.0M	Primary	t	WideOpenWest	600.0M x 50.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25907	SCC 18	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25908	SCC 19	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25910	SDS 01	\N	Midcontinent	1000.0M x 60.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25911	TNC 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25912	TNC 02	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25913	TNC 03	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25917	TNK 02	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25920	TNM 02	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25921	TNM 03	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25943	TXA 04	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25944	TXA 05	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25945	TXA 06	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25946	TXA 07	\N	Spectrum	600.0M x 35.0M	Primary	t	Astound	500.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25947	TXA 08	\N	Spectrum	600.0M x 35.0M	Primary	t	Unite Private Networks	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25949	TXA 10	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25958	TXA 19	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25960	TXA 21	\N	Altice	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25352	COX 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	f	Unknown		Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25424	GAA 25	\N	AT&T Broadband II	1000.0 M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	f	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25426	GAA 27	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25769	NMR 01	\N	Plateau Telecommunications	300.0M x 30.0M	Primary	t	Sparklight	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25750	NMA 01	\N	Unite Network	300.0M x 300.0M	Primary	t	Comcast	300.0M x 30.0M	Secondary	t	2025-07-10 11:01:53.677497	2025-07-07 09:50:02.79366	t	2025-07-10 11:01:53.677497	\N	\N	\N	\N
25376	FLO 01	\N	Spectrum	600.0M x 35.0M	Primary	f	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25711	NCC 18	\N	Spectrum	600.0M x 35.0M	Primary	f	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25964	TXC 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25965	TXC 03	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25970	TXC 08	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25971	TXC 09	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25974	TXC 12	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25975	TXC 13	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
28410	NVRB04	{Lab}	TEST STORE NOT PRODUCTION		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25978	TXC 16	\N	Altice	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25979	TXC 17	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25982	TXC 20	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25985	TXD 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25986	TXD 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25987	TXD 04	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25989	TXD 06	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25990	TXD 08	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Frontier Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25991	TXD 09	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25992	TXD 10	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25994	TXD 12	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25995	TXD 13	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25997	TXD 17	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25998	TXD 18	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25999	TXD 19	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26009	TXD 32	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26012	TXD 35	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26014	TXD 37	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26016	TXD 39	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26018	TXD 41	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26023	TXD 46	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26024	TXD 47	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Longview Cable	500.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26025	TXD 48	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26028	TXD 52	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26029	TXD 54	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26032	TXD 57	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26034	TXD 59	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Frontier Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26036	TXD 61	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26039	TXD 64	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26041	TXD 66	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26044	TXD 69	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26048	TXD 73	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26065	TXD 90	\N	East Texas Broadband	300.0M x 300.0M	Primary	t	CenturyLink/Embarq	40.0M x 5.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25721	NCC 30	\N	Spectrum	600.0M x 35.0M	Primary	f	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25310	COD 15	\N	Comcast		Primary	t	Verizon Business	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25311	COD 17	\N	Comcast		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25791	NVL W01	\N	Cox Communications		Primary	t	Unknown		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25251	CAS 06	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25256	CAS 11	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25257	CAS 12	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25260	CAS 15	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25261	CAS 16	\N	Cox Business	1000.0M x 35.0M	Primary	t	Accelerated	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25264	CAS 19	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25755	NMA 06	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 11:00:41.959651	\N	\N	\N	\N
25774	NVL 04	\N	Cox Business/BOI	300.0M x 30.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25775	NVL 05	\N	Cox Business/BOI	300.0M x 30.0M	Primary	f	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25863	OKT 06	\N	Cox Business/BOI 	300.0M x 30.0M	Primary	t	BTC Broadband	300.0M x 50.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25865	OKT 08	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Windstream Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25866	ORM 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Hunter Communications	300.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26066	TXD 91	\N	Frontier FIOS	200.0M x 200.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26067	TXD 92	\N	AT&T Broadband II	200.0M x 200.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26071	TXD 96	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26072	TXE 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26073	TXE 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26074	TXE 03	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26075	TXE 05	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	100.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26076	TXE 06	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26077	TXE 07	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26082	TXH 01	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast Workplace	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
28512	Starlink POC	{Lab}			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
28514	Strike Team Lab	{Lab}	Connected to 1B.4.4.10 Uplink to IDF1B-Core VLAN 200		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
26083	TXH 02	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26084	TXH 03	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26089	TXH 12	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26091	TXH 15	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26094	TXH 18	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26096	TXH 21	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26102	TXH 27	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26104	TXH 29	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26105	TXH 30	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25802	NYB 07	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25914	TNE 01	\N	Comcast	300.0 M	Primary	t	BrightRidge	300.0M x 30.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25300	COD 04	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25302	COD 06	\N	Lumen	100.0M x 10.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25781	NVL 13	\N	Cox Business/BOI	300.0M x 30.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25792	NVR 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25819	OHC 04	\N	Spectrum	600.0M x 35.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25831	OHN 03	\N	Spectrum	600.0M x 35.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25843	OKE 01	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	f	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26106	TXH 31	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26109	TXH 37	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26127	TXH 59	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26135	TXH 67	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26145	TXH 78	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26155	TXH 88	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26157	TXH 90	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26161	TXH 94	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Consolidated Communications	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26168	TXL 02	\N	Altice	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26169	TXL 03	\N	Altice	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26170	TXL 04	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Vexus Fiber	350.0M x 350.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26171	TXL 05	\N	Vexus	550.0M x 275.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26173	TXM 02	\N	Altice	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26175	TXN 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26176	TXO 01	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	EB2-CableOne Cable	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26177	TXO 02	\N	Cable One 	300.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26179	TXS 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26185	TXS 11	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26189	TXS 15	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26191	TXS 17	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26192	TXS 18	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Windstream Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26193	TXS 19	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26194	TXS 20	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26196	TXS 22	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26197	TXS 23	\N	Spectrum	600.0M x 35.0M	Primary	t	GVTC Communications	250.0M x 250.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26201	TXS 27	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26202	TXS 28	\N	AT&T Broadband II	500.0M x 100.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26207	TXW 02	\N	Altice	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26244	VAB 03	\N	Verizon FIOS	500.0M x 500.0M	Primary	t	DSR Cox Cable	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26247	VAB 06	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Verizon Fiber	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26248	VAB 07	\N	Verizon FIOS  	500.0M x 500.0M	Primary	t	Cox Business/BOI	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26258	VAR 05	\N	EB2-Verizon Fiber	500.0M x 500.0M	Primary	t	Comcast Workplace	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25789	NVL 25	\N	CenturyLink Fiber Plus	500.0M x 500.0M	Primary	f	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25125	AZP 63	\N	Starlink	Satellite	Primary	t	VZG Cell	Cell	Secondary	t	2025-07-09 08:44:56.798844	2025-07-07 09:50:02.79366	t	2025-07-09 08:44:56.798844	\N	\N	\N	\N
25113	AZP 50	\N	Cox Business/BOI	300.0M x 30.0M	Primary	f	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25430	GAA 31	\N	Spectrum	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25869	ORP 02	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25875	ORP 09	\N	Comcast Workplace	250.0M x 25.0M	Primary	f	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25976	TXC 14	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26264	VAW 02	\N	Cox Business/BOI	1000.0M x 50.0M	Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26265	VAW 03	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26269	WAE 03	\N	Spectrum	600.0M x 35.0M	Primary	t	Pocketinet Communications	100.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26272	WAS 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Ziply Fiber	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26273	WAS 02	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	Accelerated	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26275	WAS 04	\N	Centurylink Fiber-Plus	500.0M x 500.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26277	WAS 06	\N	CenturyLink Fiber Plus	500.0M x 500.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26278	WAS 08	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26282	WAS 13	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Astound	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26284	WAS 15	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-09 15:58:49.918176	\N	\N	\N	\N
26285	WAS 17	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Ziply Fiber | NAM Fiber |	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26287	WAS 19	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26290	WAS 22	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26294	WAS 26	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	EB2-Ziply Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-07 10:26:11.509196	\N	\N	\N	\N
26295	WAS 27	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	CenturyLink/Qwest	10.0M x 2.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26297	WAS 29	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26299	WAV 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26307	WIA 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26309	WIC 01	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26310	WIE 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26311	WIE 02	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26313	WIL 01	\N	Spectrum	600.0M x 35.0M	Primary	t	MetroNet	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26315	WIM 02	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26316	WIM 03	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26317	WIM 04	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26318	WIM 05	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26321	WIW 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26322	WVE 01	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26323	WYO 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26324	WYO 02	\N	Spectrum	300.0M x 20.0M	Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26325	WYO 03	\N	Mountain West Technologies	500.0M x 500.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25047	ARL 02	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25240	CAN W02	\N	AT&T Enterprises, LLC		Primary	t			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25103	AZP 39	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25299	COD 03	\N	Comcast	\N	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25304	COD 08	\N	Comcast	\N	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25343	COS 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25388	FLO 13	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25941	TXA 02	\N	Spectrum	600.0M x 35.0M	Primary	f	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25950	TXA 11	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25053	ARO 02	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25406	GAA 01	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25444	GAA 45	\N	AT&T Broadband II	300.0M x 20.0M	Primary	t	Mediacom/BOI	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25445	GAA 46	\N	Mediacom/BOI	2000.0M x 2000.0M	Primary	t	AT&T Broadband II	1000.0M x 30.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25627	MIP 01	\N	Winn Telecom	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 100.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25316	COD 22	\N	Comcast Cable Communications, LLC		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26239	UTS 26	\N	Infowest Inc	250.0M x 250.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-09 16:18:29.92789	2025-07-07 09:50:02.79366	t	2025-07-09 16:18:29.92789	\N	\N	\N	\N
25115	AZP 53	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25107	AZP 44	\N	CenturyLink	100.0M x 10.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:51:54.378377	2025-07-07 09:50:02.79366	t	2025-07-07 11:51:54.378377	\N	\N	\N	\N
25670	MOO 01	\N	ComcastAgg CableOne	300.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-09 11:43:17.144937	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25274	CAS 32	\N	Spectrum	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25485	ILC 09	\N	Comcast	300.0M x 35.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-09 15:09:11.623933	2025-07-07 09:50:02.79366	t	2025-07-09 15:09:11.623933	\N	\N	\N	\N
25491	ILC 16	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-09 15:10:07.466937	\N	\N	\N	\N
25673	MOO 04	\N	Brightspeed	\N	Primary	t	Verizon	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25694	NCC_00	\N	Charter Communications	\N	Primary	t			Secondary	f	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25759	NMA 10	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25872	ORP 05	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26227	UTS 14	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	First Digital	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26230	UTS 17	\N	Comcast	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26233	UTS 20	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	First Digital	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26234	UTS 21	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26236	UTS 23	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26240	UTS W01	\N	Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26241	UTS W02	\N	DSR Comcast Cable	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
28883	VISION_Store0	{Lab}	Cox Communications		Primary	f	Unknown		Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
28884	VISION_Test_Lab_MinesW	{Lab}	SW03 relocated to the Vison test lab		Primary	f	Unknown		Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
26254	VAR 01	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26267	WAE 01	\N	Comcast	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26268	WAE 02	\N	Comcast	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26279	WAS 09	\N	Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26280	WAS 11	\N	Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26283	WAS 14	\N	Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25155	CAL 14	\N	DSR One Ring Networks | Fixed Wireless |	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26225	UTS 12	\N	DSR TDS Cable - 3rd Party Cable Ordered Speed	500.0M x 100.0M	Primary	t	Digi Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25104	AZP 41	\N	AT&T	\N	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-09 06:49:23.953543	\N	\N	\N	\N
25208	CAN 29	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25211	CAN 32	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25215	CAN 36	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:28:43.873237	\N	\N	\N	\N
28933	West Store Test	{Lab}	Unknown		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
28934	Wyomissing Voice	{Voice}	AT&T BVOIP Asset ID IZEC561531ATI		Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
25231	CAN 52	\N	Consolidated Communications	300.0M x 300.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25348	COS 06	\N	Comcast Workplace	600.0M x 35.0M	Primary	f	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25522	INC 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	f	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26251	VAF 01 - appliance	\N	Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26298	WAS W00	\N	Comcast	\N	Primary	t	Digi Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-07 10:25:33.442318	\N	\N	\N	\N
26306	WDTD 01	\N	AT&T	\N	Primary	t	ATT	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25465	IAN 03	\N	Mediacom Communications Corporation	1000.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26055	TXD 80	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 19:52:42.078794	2025-07-07 09:50:02.79366	t	2025-07-10 19:52:42.078794	\N	\N	\N	\N
25131	AZT 06	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25486	ILC 11	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-09 15:09:37.78576	\N	\N	\N	\N
26030	TXD 55	\N	Spectrum	600.0M x 35.0M	Primary	f	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26031	TXD 56	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26062	TXD 87	\N	Frontier FIOS	500.0M x 500.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25296	COD_00	\N	Comcast Cable Communications, LLC		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26116	TXH 48	\N	Optimum	500.0M x 50.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 13:16:48.861946	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25239	CAN 61	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast Workplace	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25262	CAS 17	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25338	COG 03	\N	Spectrum	600.0M x 35.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25339	CON 02	\N	Comcast Workplace	250.0M x 25.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26092	TXH 16	\N	Comcast Workplace	600.0M x 35.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26122	TXH 54	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26112	TXH 43	\N	AT&T Enterprises, LLC	500.0M x 50.0M	Primary	t	Optimum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25322	COD 28	\N	Comcast Workplace	1000.0M x 35.0M	Primary	t	AT&T	20.0 M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26619	Corporate Store0	{Vision}	Corporate Store 0 Replica requested by Paul Higel Located in Endpoint Room Named MAR_01 in AD TEST STORE		Primary	f	Unknown		Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 10:54:59.444946	f	\N	\N	\N	\N	\N
25354	Desert Ridge Building I Security	\N			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25510	ILC 41	\N	Comcast Cable Communications, LLC		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25317	COD 23	\N	Comcast	300.0M x 35.0M	Primary	t	EB2-Lumen DSL	100.0M x 10.0M	Secondary	t	2025-07-09 15:04:48.239555	2025-07-07 09:50:02.79366	t	2025-07-09 15:04:48.239555	\N	\N	\N	\N
25516	ILP 01	\N	i3 Broadband	250.0M x 250.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-09 15:59:20.282672	2025-07-07 09:50:02.79366	t	2025-07-09 15:59:20.282672	\N	\N	\N	\N
25144	CAL 03	\N	GTT Ethernet	200.0M x 200.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 13:22:39.168204	2025-07-07 09:50:02.79366	t	2025-07-10 13:22:39.168204	\N	\N	\N	\N
25527	INF 01	\N	Comcast	300.0M x 30.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 13:57:14.60453	2025-07-07 09:50:02.79366	t	2025-07-10 13:57:14.60453	\N	\N	\N	\N
25123	AZP 61	\N	Cox Business/BOI	200.0M x 20.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25130	AZT 03	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25138	AZT 14	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Login, Inc.	100.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25139	AZY 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25151	CAL 10	\N	Spectrum	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25158	CAL 18	\N	Spectrum	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25301	COD 05	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Comcast Workplace	750.0 M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25306	COD 10	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Comcast Workplace	500.0 M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25308	COD 13	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25315	COD 21	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	CenturyLink/Qwest	40.0M x 5.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25319	COD 25	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Centurylink DSL	140.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25320	COD 26	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Centurylink DSL	80.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25326	COD 32	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	CenturyLink/Qwest	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25070	AZP 01	\N	Cox Business/BOI	300.0M x 30.0M	Primary	f	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25383	FLO 08	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25385	FLO 10	\N	Spectrum	600.0M x 35.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25524	INC 03	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26146	TXH 79	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26142	TXH 74	\N	Optimum	500.0M x 50.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25407	GAA 03	\N	Private Customer - AT&T Internet Services	250.0M x 25.0M	Primary	t	Comcast Cable Communications, LLC	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25440	GAA 41	\N	Comcast Workplace	250.0M x 25.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25442	GAA 43	\N	AT&T	\N	Primary	t	Spectrum	1000.0M x 50.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:36:49.58417	\N	\N	\N	\N
25451	GAN 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25543	INI 14	\N	Comcast Workplace	600.0M x 35.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25156	CAL 15	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25159	CAL 19	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25540	INI 10	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25403	FP-DAL-OOBMGMT-01	\N	Unknown		Primary	t	Unknown		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25404	FP-DAL-OOBMGMT-02	\N	Unknown		Primary	t	Unknown		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25362	Flight Department	\N	Cox Communications Inc.		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26867	LAB 04	{Discount-Tire}	: AT&T Broadband II	1000.0M x 1000.0M	Primary	f			Secondary	f	2025-07-07 11:46:54.544083	2025-07-07 10:54:59.444946	f	\N	\N	\N	\N	\N
25578	MIA 17	\N	D & P Communications	1000.0 M	Primary	t	Comcast	1000.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25278	CAS 36	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25377	FLO 02	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25574	LAS 03	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:40:02.038067	\N	\N	\N	\N
25579	MIAC02	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25581	MID 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25453	HPL_00	\N	This is a one man office for Todd Richards.		Primary	t	Unknown		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25147	CAL 06	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25152	CAL 11	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25153	CAL 12	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25598	MID 23	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25622	MIL 11	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:59:32.835764	\N	\N	\N	\N
25624	MIL 28	\N	Comcast Direct	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25626	MIN 01	\N	Spectrum	300.0M x 20.0M	Primary	t	Accelerated 6335-MX SN 6335011175511770	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:59:57.491017	\N	\N	\N	\N
25646	MNM 14	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25649	MNM 17	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25650	MNM 18	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Accelerated	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25658	MNM 26	\N	Comcast Workplace	600.0M x 35.0M	Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25651	MNM 19	\N	DSR MetroNet Fiber	300.0M x 300.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25677	MOS 02	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	AT&T	20.0M x 20.0M	Secondary	t	2025-07-10 19:43:28.589236	2025-07-07 09:50:02.79366	t	2025-07-10 19:43:28.589236	\N	\N	\N	\N
26293	WAS 25	\N			Primary	f	AT&T Cell	cell	Secondary	t	2025-07-10 13:16:48.861946	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25353	Desert Ridge	\N	Cox Network 500 Circuit ID 23.HMXX.126497 Acct 2318296-02 AT&T ADI	100.0 M	Primary	t			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25500	ILC 28	\N	Comcast	300.0M x 30.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 13:57:53.002512	2025-07-07 09:50:02.79366	t	2025-07-10 13:57:53.002512	\N	\N	\N	\N
25282	CAS 40	\N	Frontier	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25289	CAS 47	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25653	MNM 21	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25707	NCC 14	\N	Spectrum	600.0M x 35.0M	Primary	f	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25511	ILC 42	\N	Oswego Static /32		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25512	ILC 43	\N	Comcast Cable Communications, LLC		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25513	ILC 44	\N	Static pool - Cinergy MetroNet		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25514	ILC 45	\N	Comcast Cable Communications, LLC		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25772	NVL_00	\N	Cox Communications		Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25546	INI W01	\N	Comcast Cable Communications, LLC		Primary	t	Private Customer - AT&T Internet Services		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25528	INF 02	\N	Comcast	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 13:58:25.463012	2025-07-07 09:50:02.79366	t	2025-07-10 13:58:25.463012	\N	\N	\N	\N
25169	CAL 33	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25283	CAS 41	\N	Frontier	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-07 11:09:27.46099	\N	\N	\N	\N
25288	CAS 46	\N	AT&T	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25297	COD 01	\N	Comcast	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25298	COD 02	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25303	COD 07	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25307	COD 11	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25356	FLD 02	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25358	FLF 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-09 16:03:27.107277	\N	\N	\N	\N
25661	MNM 31	\N	Comcast Workplace	300.0M x 30.0M	Primary	t			Secondary	f	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25682	MOS 07	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25684	MOS 09	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25685	MOS 10	\N	Spectrum	600.0M x 35.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25726	NCC 38	\N	MetroNet	1000.0 M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 18:58:22.643651	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25737	NCC 51	\N	Altice West	100.0M x 10.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25754	NMA 05	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25736	NCC 48	\N	Brightspeed	300.0 M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 18:58:22.643786	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25037	ALB 03	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25073	AZP 07	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25305	COD 09	\N	Comcast	\N	Primary	t	VZW Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25309	COD 14	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25386	FLO 11	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25719	NCC 27	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25732	NCC 44	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25733	NCC 45	\N	Spectrum	600.0M x 35.0M	Primary	t	Brightspeed	100.0M x 100.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25740	NDG 01	\N	Midcontinent	500.0M x 50.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25752	NMA 03	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25756	NMA 07	\N	Comcast Workplace	1000.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25767	NMH 01	\N	Windstream	500.0M x 500.0M	Primary	t	EB2-TDS Cable	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25773	NVL 03	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 19:43:54.803914	2025-07-07 09:50:02.79366	t	2025-07-10 19:43:54.803914	\N	\N	\N	\N
25613	MIG 25	\N	Comcast		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25762	NMA 13	\N	Unite Private Networks	300.0 M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 18:58:22.643913	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25776	NVL 06	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 19:44:18.415077	2025-07-07 09:50:02.79366	t	2025-07-10 19:44:18.415077	\N	\N	\N	\N
25662	MNM W01	\N	Comcast		Primary	t	Unknown		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25788	NVL 24	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	CenturyLink	10.0M x 1.0M	Secondary	t	2025-07-10 19:45:06.729903	2025-07-07 09:50:02.79366	t	2025-07-10 19:45:06.729903	\N	\N	\N	\N
25777	NVL 07	\N	Cox Communications	300.0 M	Primary	t	Verizon Business	300.0M x 30.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25648	MNM 16	\N	Comcast	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:00:37.809961	2025-07-07 09:50:02.79366	t	2025-07-10 14:00:37.809961	\N	\N	\N	\N
25096	AZP 32	\N	Cox Business/BOI	200.0M x 20.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25173	CAL 40	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25344	COS 02	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25636	MNM 03	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25757	NMA 08	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25761	NMA 12	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25764	NMAW00	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25768	NML 01	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25779	NVL 09	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25780	NVL 11	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25782	NVL 14	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25785	NVL 17	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25786	NVL 22	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25787	NVL 23	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25790	NVL 26	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25687	MOSW 01	\N	arco trucking08162011143812942		Primary	t	Charter Communications LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25688	MSG 01	\N			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25834	OHN 06	\N	Armstrong Cable	300.0M x 300.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25119	AZP 57	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25132	AZT 07	\N	Cox Business	200.0M x 200.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25312	COD 18	\N	Comcast Workplace	1000.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25313	COD 19	\N	CenturyLink Fiber Plus	500.0M x 500.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25835	OHS 01	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25763	NMACALLCNTR	\N	Comcast Cable Communications, LLC		Primary	t			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25873	ORP 07	\N	Ziply Fiber	1000.0M x 1000.0M	Primary	t	Accerated AT&T	Cell	Secondary	t	2025-07-10 19:45:31.582614	2025-07-07 09:50:02.79366	t	2025-07-10 19:45:31.582614	\N	\N	\N	\N
25874	ORP 08	\N	DSR TDS Cable	300.0M x 30.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25881	PAN 02	\N	DSR EB2-Penteledata Cable - NAM Cable -	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25885	PAP 01	\N	EB2-RCN Cable	250.0M x 15.0M	Primary	t	PenTeleData House Account	200.0M x 25.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25892	SCC 03	\N	Comporium Com DDSL | Dedicated Line ADSL Dry Loop |	1000.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25314	COD 20	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25877	ORP 11	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25878	ORP 12	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25880	PAN 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25886	PAP 02	\N	Comcast Workplace	600.0M x 35.0M	Primary	t			Secondary	f	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25887	PAW 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25888	PAW 02	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25902	SCC 13	\N	Hargray Telephone Co.	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25956	TXA 17	\N	Spectrum	750.0M x 35.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 19:46:31.427635	2025-07-07 09:50:02.79366	t	2025-07-10 19:46:31.427635	\N	\N	\N	\N
25844	OKO_00	\N			Primary	f	Cox Communications	300.0 M	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25797	NYB 02	\N	DUNN TIRE		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25287	CAS 45	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-09 15:03:11.500931	2025-07-07 09:50:02.79366	t	2025-07-09 15:03:11.500931	\N	\N	\N	\N
25798	NYB 03	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25799	NYB 04	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25803	NYB 08	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25804	NYF 01	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25805	NYF 02	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25806	NYF 03	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25807	NYR 01	\N			Primary	f	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25808	NYR 02	\N	Charter Communications Inc		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25809	NYR 03	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25812	NYR 06	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25813	NYR 07	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25814	NYS 01	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25923	TNM 05	\N	Spectrum 	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25929	TNN 06	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25931	TNN 08	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25926	TNN 03	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25927	TNN 04	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25928	TNN 05	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25930	TNN 07	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25932	TNN 09	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25933	TNN 10	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25935	TNN 12	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25925	TNN 02	\N	AT&T Broadband II	1000.0 M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	f	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25940	TXA 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25957	TXA 18	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25961	TXA 22	\N	Spectrum	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25934	TNN 11	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25937	TNN 14	\N	AT&T Broadband II	940.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25938	TNN 15	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25882	PAN 03	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25883	PAN 04	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25884	PAN 05	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
27187	Store in a box #2	{Discount}			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 10:54:59.444946	f	\N	\N	\N	\N	\N
25265	CAS 20	\N	Spectrum	200.0M x 10.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25291	CAS 49	\N	Spectrum	600.0M x 35.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25318	COD 24	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25321	COD 27	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Accelerated AT&T	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 11:02:33.27892	\N	\N	\N	\N
25458	IAD 03	\N	EB2-Centurylink Fiber	500.0M x 100.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25868	ORP 01	\N	Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25936	TNN 13	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25939	TNN 16	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II 	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25942	TXA 03	\N	Spectrum	600.0M x 35.0M	Primary	t	Spectrum	750.0 M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25290	CAS 48	\N	Frontier Communications	500.0M x 500.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25331	COD 38	\N	CenturyLink	100.0M x 10.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-09 17:20:57.996898	2025-07-07 09:50:02.79366	t	2025-07-09 17:20:57.996898	\N	\N	\N	\N
25325	COD 31	\N	MallCom Networks	300.0M x 30.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 13:16:48.861946	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25323	COD 29	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25327	COD 34	\N	Lumen/Qwest	100.0M x 10.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25919	TNM 01	\N	Comcast		Primary	t	Verizon Business	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25330	COD 37	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25332	COD 39	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25488	ILC 13	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25951	TXA 12	\N	Frontier	\N	Primary	f	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25953	TXA 14	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25954	TXA 15	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25955	TXA 16	\N	Spectrum	600.0M x 35.0M	Primary	t	Unite Private Networks	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25959	TXA 20	\N	Spectrum	600.0M x 35.0M	Primary	t	NORTHLAND CABLE TELEVISION INC.	250.0M x 25.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25490	ILC 15	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25334	COD 41	\N	Lumen	300.0M x 300.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-09 11:43:17.144937	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25335	COD 42	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25341	COP 02	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25996	TXD 15	\N	Spectrum	300.0M x 20.0M	Primary	f	VZW Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26005	TXD 28	\N	Spectrum	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25346	COS 04	\N	CenturyLink Fiber Plus	500.0M x 500.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25349	COS 07	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25350	COW 01	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:31:34.68083	\N	\N	\N	\N
25372	FLJ 11	\N	AT&T Broadband II	500.0M x 100.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26006	TXD 29	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26007	TXD 30	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25811	NYR 05	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25784	NVL 16	\N	VZW Cell	Cell	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26061	TXD 86	\N	Spectrum	600.0M x 35.0M	Primary	t	ACCELERATED	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26026	TXD 50	\N	Private Customer - AT&T Internet Services	600.0M x 35.0M	Primary	t	Charter Communications Inc	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25061	AZH 01	\N	Optimum	500.0M x 50.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25064	AZN 02	\N	CABLE ONE, INC.	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25068	AZN 06	\N	Sparklight	300.0M x 30.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26090	TXH 14	\N	Comcast Cable Communications, LLC		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26051	TXD 76	\N	Contrera	300.0M x 150.0M	Primary	t	Altice	500.0M x 50.0M	Secondary	t	2025-07-08 18:24:12.685433	2025-07-07 09:50:02.79366	t	2025-07-08 18:24:12.685433	\N	\N	\N	\N
25058	AZC 01	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25063	AZM 01	\N	Orbitel Communications	300.0M x 20.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25066	AZN 04	\N	AT&T	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-07 11:49:51.480822	\N	\N	\N	\N
25076	AZP 10	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25077	AZP 11	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25078	AZP 13	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25084	AZP 20	\N	Saddleback Communications	300.0M x 80.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25089	AZP 25	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26166	TXH W00	\N	Comcast Cable Communications, LLC		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26153	TXH 86	\N	Comcast	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26152	TXH 85	\N	Optimum	500.0M x 50.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25817	NYS 04	\N	DUNN TIRE		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25515	ILC 46	\N	Comcast Cable Communications, LLC		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26178	TXS_00	\N	Private Customer - AT&T Internet Services		Primary	t	Charter Communications Inc		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26226	UTS 13	\N	Comcast		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26158	TXH 91	\N	Livcom	200.0M x 200.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 10:59:25.936361	2025-07-07 09:50:02.79366	t	2025-07-10 10:59:25.936361	\N	\N	\N	\N
26159	TXH 92	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	CenturyLink Communications, LLC	80.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26163	TXH 96	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
28767	TXH SE Flex DTU	{Lab}	Comcast Workplace	600.0M x 35.0M	Primary	f			Secondary	f	2025-07-10 14:22:08.521283	2025-07-07 11:46:47.102071	f	\N	\N	\N	\N	\N
26164	TXH 97	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Comcast	600.0M x 35.0M	Secondary	t	2025-07-10 19:55:45.018876	2025-07-07 09:50:02.79366	t	2025-07-10 19:55:45.018876	\N	\N	\N	\N
26291	WAS 23	\N	ComcastAgg CLink	10.0M x 1.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-09 11:43:17.144937	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26276	WAS 05	\N	Starlink Serial KITP00174439	Satellite	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-09 15:58:08.181017	2025-07-07 09:50:02.79366	t	2025-07-09 15:58:08.181017	\N	\N	\N	\N
25059	AZF 01	\N	DSR CLink Fiber	500.0M x 500.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 13:16:48.861946	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25081	AZP 17	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25228	CAN 49	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26215	UTS_00	\N	Discount Tire - UTS 00		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26266	VAW 04	\N			Primary	t			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26274	WAS 03	\N	Comcast		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25233	CAN 54	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25324	COD 30	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25359	FLG 01	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25380	FLO 05	\N	Spectrum	600.0M x 35.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26281	WAS 12	\N	Starlink	Satellite	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25447	GAA W00	\N	AT&T Broadband II	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25277	CAS 35	\N	Frontier	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25517	ILR 01	\N	Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-09 15:41:26.81457	\N	\N	\N	\N
25551	INW 02	\N	Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26292	WAS 24	\N	Comcast		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26271	WAS_00	\N	Ziply Fiber		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26301	WAX 01	\N			Primary	f			Secondary	f	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26303	WDCA 01	\N	Frontier Communications Corporation		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26304	WDGA01	\N	Private Customer - AT&T Internet Services		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25603	MID W00	\N	DSR - MIHW00		Primary	t	Unknown		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25800	NYB 05	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25801	NYB 06	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25810	NYR 04	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25796	NYB 01	\N	DUNN TIRE		Primary	t	AT&T Enterprises, LLC		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25815	NYS 02	\N	DUNN TIRE		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25816	NYS 03	\N	DUNN TIRE		Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25984	TXD_00	\N	DSR Road Runner BOC | Extended Cable |	600.0 M	Primary	t	Unknown		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25069	AZP_00	\N	Cox Communications	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-09 06:49:56.715964	2025-07-07 09:50:02.79366	t	2025-07-09 06:49:56.715964	\N	\N	\N	\N
26100	TXH 25	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26103	TXH 28	\N	Comcast	\N	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26113	TXH 44	\N	Comcast	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26132	TXH 64	\N	Comcast	\N	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26305	WDIL 01	\N	Comcast Cable Communications, LLC		Primary	t	Private Customer - AT&T Internet Services		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26138	TXH 70	\N	Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26217	UTS 02	\N	Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26228	UTS 15	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26232	UTS 19	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25040	ALM 03	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26046	TXD 71	\N	AT&T Broadband II	300.0 M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 18:58:22.644435	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26255	VAR 02	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-11 02:56:24.838971	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26060	TXD 85	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26242	VAB 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26253	VAR_00	\N	Comcast	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-09 16:18:08.309988	2025-07-07 09:50:02.79366	t	2025-07-09 16:18:08.309988	\N	\N	\N	\N
25487	ILC 12	\N	Comcast	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26040	TXD 65	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26043	TXD 68	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26045	TXD 70	\N	Spectrum	940.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26047	TXD 72	\N	AT&T Broadband II	500.0M x 100.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26053	TXD 78	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26057	TXD 82	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26059	TXD 84	\N	VyVe	500.0M x 50.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26243	VAB 02	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26245	VAB 04	\N	Verizon FIOS	500.0M x 500.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26246	VAB 05	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26249	VAB 08	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26250	VAB 09	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Accelerated	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26252	VAF 02	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26257	VAR 04	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26259	VAR 06	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Accelerated	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26260	VAR 07	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26262	VAT 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Point Broadband	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26288	WAS 20	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26289	WAS 21	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26167	TXL 01	\N	Vexus	500.0M x 50.0M	Primary	t	Altice West	250.0M x 250.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25275	CAS 33	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25279	CAS 37	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25503	ILC 31	\N	Comcast Workplace\t	750.0M x 35.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-08 10:26:51.066045	2025-07-07 09:50:02.79366	t	2025-07-08 10:26:51.066045	\N	\N	\N	\N
25384	FLO 09	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25391	FLO 16	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26097	TXH 22	\N	Altice	500.0M x 50.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25393	FLP 02	\N	AT&T Broadband II	200.0M x 200.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25397	FLS 02	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Accelerated	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25410	GAA 07	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25505	ILC 33	\N	AT&T Broadband II	1000.0M x 200.0M	Primary	t	Accelerated AT&T	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 11:03:06.659517	\N	\N	\N	\N
25518	ILR 02	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25394	FLP 03	\N	AT&T Broadband II	300.0M x 20.0M	Primary	t	x	300.0M x 300.0M	Secondary	f	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25534	INI 03	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-09 15:44:03.40765	2025-07-07 09:50:02.79366	t	2025-07-09 15:44:03.40765	\N	\N	\N	\N
25441	GAA 42	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25536	INI 06	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25559	KSK 06	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-10 13:59:11.548478	\N	\N	\N	\N
25915	TNE 02	\N	Spectrum 	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25691	MTB 01	\N	Spectrum 	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25692	MTM 01	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25712	NCC 19	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25714	NCC 21	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25820	OHC 05	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25826	OHD 03	\N	Spectrum	940.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25916	TNK 01	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25864	OKT 07	\N	AT&T Broadband II	500.0M x 100.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25871	ORP 04	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25903	SCC 14	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25909	SDR 01	\N	Midcontinent	500.0M x 500.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26079	TXG 02	\N	Consolidated Communications	300.0 M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 18:58:22.645231	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26000	TXD 20	\N	Spectrum	750.0M x 35.0M	Primary	t	Accelerated AT&T	Cell	Secondary	t	2025-07-10 19:52:03.187294	2025-07-07 09:50:02.79366	t	2025-07-10 19:52:03.187294	\N	\N	\N	\N
25918	TNK 03	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25962	TXA 23	\N	Spectrum	300.0M x 20.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25966	TXC 04	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25967	TXC 05	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25972	TXC 10	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25988	TXD 05	\N	Spectrum	940.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26002	TXD 23	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26003	TXD 25	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25963	TXA 24	\N	Spectrum	750.0 M	Primary	t	AT&T Enterprises, LLC	600.0M x 35.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26010	TXD 33	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	f	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26011	TXD 34	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26013	TXD 36	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26020	TXD 43	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26035	TXD 60	\N	Spectrum Business	500.0M x 500.0M	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26037	TXD 62	\N	Cable One	300.0M x 50.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26070	TXD 95	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26078	TXG 01	\N	AT&T Broadband II	2000.0M x 2000.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26008	TXD 31	\N	Spectrum	750.0M x 35.0M	Primary	t	AT&T Cell	Cell	Secondary	t	2025-07-10 19:52:23.086581	2025-07-07 09:50:02.79366	t	2025-07-10 19:52:23.086581	\N	\N	\N	\N
26085	TXH 04	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26098	TXH 23	\N	Optimum	500.0M x 50.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26114	TXH 45	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26108	TXH 34	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-09 16:02:22.593714	2025-07-07 09:50:02.79366	t	2025-07-09 16:02:22.593714	\N	\N	\N	\N
26080	TXG 03	\N	Comcast Workplace\t	750.0M x 35.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-09 16:04:57.594998	2025-07-07 09:50:02.79366	t	2025-07-09 16:04:57.594998	\N	\N	\N	\N
26101	TXH 26	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26115	TXH 46	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26117	TXH 49	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26118	TXH 50	\N	AT&T Broadband II	300.0M x 300.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26119	TXH 51	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26125	TXH 57	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Cell	cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26123	TXH 55	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast Cable Communications, LLC	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25333	COD 40	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25605	MIF 05	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25635	MNM 02	\N	Comcast	\N	Primary	t	Starlink	Satellite	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25641	MNM 09	\N	DSR Comcast	\N	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25643	MNM 11	\N	Comcast	\N	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25656	MNM 24	\N	Comcast	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25660	MNM 29	\N	Comcast	\N	Primary	t	Verizon Business	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26131	TXH 63	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26147	TXH 80	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26136	TXH 68	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26139	TXH 71	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26141	TXH 73	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26208	TXW 03	\N	Optimum	500.0M x 50.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26211	TXW 06	\N	Optimum	500.0M x 50.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26143	TXH 75	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26150	TXH 83	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26172	TXM 01	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26183	TXS 08	\N	Spectrum	940.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26199	TXS 25	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26216	UTS 01	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25657	MNM 25	\N	ComcastAgg		Primary	t	Verizon Business	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25633	MNM_00	\N	Comcast	600.0 M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26220	UTS 05	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Centracom	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26229	UTS 16	\N	Comcast	300.0M x 30.0M	Primary	t	EB2-Lumen DSL	100.0M x 10.0M	Secondary	t	2025-07-09 16:18:57.402086	2025-07-07 09:50:02.79366	t	2025-07-09 16:18:57.402086	\N	\N	\N	\N
26221	UTS 06	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	EB2-Centurylink DSL	80.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26224	UTS 11	\N	Comcast	300.0M x 30.0M	Primary	t	Centracom	300.0M x 30.0M	Secondary	t	2025-07-09 16:19:20.454192	2025-07-07 09:50:02.79366	t	2025-07-09 16:19:20.454192	\N	\N	\N	\N
26312	WIG 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25190	CAN 10	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-07 10:13:19.699101	\N	\N	\N	\N
25366	FLJ 03	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25532	INI 01	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast Workplace	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25566	KSW 03	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26209	TXW 04	\N	Altice	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26210	TXW 05	\N	Altice	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26212	TXW 07	\N	Altice West	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26213	TXW 08	\N	Harris Broadband	500.0M x 20.0M	Primary	t	Unite Private Networks	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26218	UTS 03	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Lumen DSL	140.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26219	UTS 04	\N	Comcast Workplace	250.0M x 25.0M	Primary	t	EB2-Lumen DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26223	UTS 09	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26231	UTS 18	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26235	UTS 22	\N	Centracom	500.0M x 500.0M	Primary	t	CenturyLink/Qwest	60.0M x 5.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26237	UTS 24	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Spanish Fork Community Network	1000.0M x 1000.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26214	TXW 09	\N	Altice	500.0M x 50.0M	Primary	t	Vexus	100.0M x 100.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26222	UTS 07	\N	Comcast	300.0 M	Primary	t	DSR Lumen DSL	80.0M x 10.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25529	INF 03	\N	MetroNet	250.0M x 25.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26238	UTS 25	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Centracom	100.0M x 40.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26300	WAV 02	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	Digi	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26302	WAY 01	\N	Spectrum	600.0M x 35.0M	Primary	t	VZW Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26314	WIM 01	\N	Spectrum	600.0M x 35.0M	Primary	t	Accelerated Cell	Cell	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25186	CAN 03	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25194	CAN 14	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	1000.0M x 200.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25207	CAN 28	\N	EB2-Frontier Fiber	600.0M x 35.0M	Primary	t	Comcast Workplace	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25210	CAN 31	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25216	CAN 37	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 200.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25232	CAN 53	\N	Vast Networks	250.0M x 25.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25250	CAS 05	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 200.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25253	CAS 08	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25259	CAS 14	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25242	CAO 03	\N	EB2-Frontier Fiber	50.0M x 10.0M	Primary	t	GTT Ethernet	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25244	CAO 06	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25248	CAS 03	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25249	CAS 04	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25237	CAN 58	\N	Private Customer - AT&T Internet Services	250.0M x 25.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25328	COD 35	\N	Comcast Workplace	75.0M x 15.0M	Primary	t	LiveWire Net	300.0M x 30.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25347	COS 05	\N	Unite Private Networks	250.0M x 25.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25360	FLG 02	\N	Ocala Fiber Network	300.0M x 30.0M	Primary	t	Cox Business/BOI	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25416	GAA 14	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25556	KSK 03	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25557	KSK 04	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25596	MID 20	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25599	MID 24	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25600	MID 25	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25109	AZP 46	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	140.0M x 20.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25604	MIF 04	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25607	MIF 26	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25631	MIT 26	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25637	MNM 05	\N	Comcast		Primary	t	DSR Lumen DSL	100.0M x 10.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25632	MIW 21	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25652	MNM 20	\N	MetroNet	600.0M x 35.0M	Primary	t	Spectrum	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25663	MOK 01	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25686	MOS 12	\N	Private Customer - AT&T Internet Services	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25681	MOS 06	\N	Spectrum	200.0M x 40.0M	Primary	t	AT&T Broadband II	600.0M x 35.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25742	NEL 01	\N	Customer Static IP Range at LNK02-OA01	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25771	NMS 03	\N	NMSurf Inc.	250.0M x 25.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25783	NVL 15	\N	Cox Business/BOI	300.0 M	Primary	t	CenturyLink	300.0M x 30.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25795	NVR 05	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25821	OHC 06	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25823	OHC 08	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25977	TXC 15	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-CableOne Cable	300.0M x 30.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25980	TXC 18	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 200.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25981	TXC 19	\N	Vexus	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25983	TXC 21	\N	Big Bend Telephone	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26038	TXD 63	\N	EB2-Windstream Fiber	300.0M x 50.0M	Primary	t	Cable One	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26068	TXD 93	\N	DSR Altice	100.0M x 10.0M	Primary	t	DSR CLink DSL	80.0 M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26069	TXD 94	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26088	TXH 11	\N	Comcast Cable Communications, LLC		Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26093	TXH 17	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26095	TXH 20	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26099	TXH 24	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26154	TXH 87	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26156	TXH 89	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26162	TXH 95	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26174	TXM 03	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Altice	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26186	TXS 12	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	750.0 M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26187	TXS 13	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26188	TXS 14	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26190	TXS 16	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25060	AZF 02	\N	Altice West	500.0M x 50.0M	Primary	t	Lightpath	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25036	ALB 01	\N	AT&T Broadband II	200.0M x 200.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	t	2025-07-07 10:49:53.914592	\N	\N	\N	\N
26256	VAR 03	\N	EB2-Verizon Fiber	300.0M x 30.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26263	VAW 01	\N	Lumos Networks	300.0M x 30.0M	Primary	t	Comcast Workplace	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26270	WAE 04	\N	EB2-Ziply Fiber	600.0M x 35.0M	Primary	t	Spectrum	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26286	WAS 18	\N	LocalTel	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26296	WAS 28	\N	Astound	300.0M x 30.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26261	VAR 08	\N	Verizon	Cell	Primary	t	Comcast		Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25405	GAA_00	\N	AT&T	1000.0 M	Primary	t	Comcast	750.0 M	Secondary	t	2025-07-07 11:46:47.102071	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25608	MIG 07	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26042	TXD 67	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25263	CAS 18	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25270	CAS 25	\N	AT&T Broadband II	940.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25272	CAS 28	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25276	CAS 34	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25280	CAS 38	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25286	CAS 44	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25292	CAS 50	\N	EB2-Frontier Fiber	50.0M x 10.0M	Primary	t	GTT Ethernet	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25340	CON 03	\N	FORT COLLINS CONNEXION	300.0M x 30.0M	Primary	t	Comcast Workplace	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25370	FLJ 09	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25088	AZP 24	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	EB2-Centurylink DSL	100.0M x 10.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25675	MOS_00	\N	Charter Communications	750.0M x 35.0M	Primary	t	AT&T	1000.0M x 1000.0M	Secondary	t	2025-07-09 17:20:30.147459	2025-07-07 09:50:02.79366	t	2025-07-09 17:20:30.147459	\N	\N	\N	\N
25267	CAS 22	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25268	CAS 23	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25269	CAS 24	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25271	CAS 27	\N	Cox Business/BOI	300.0M x 30.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25378	FLO 03	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25382	FLO 07	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25400	FLT 01	\N	Comcast	300.0M x 300.0M	Primary	t	MetroNet	300.0 M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25401	FLT 02	\N	Comcast	300.0 M	Primary	t	MetroNet	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25408	GAA 05	\N	Comcast	300.0M x 300.0M	Primary	t	AT&T Broadband II	300.0 M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25411	GAA 08	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25412	GAA 10	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25414	GAA 12	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25415	GAA 13	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25417	GAA 15	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25419	GAA 18	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25420	GAA 19	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25427	GAA 28	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25429	GAA 30	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25432	GAA 33	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25433	GAA 34	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25434	GAA 35	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25435	GAA 36	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25436	GAA 37	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25439	GAA 40	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25452	GAS 01	\N	AT&T Broadband II	1000.0M x 30.0M	Primary	t	Mediacom Communications Corporation	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25457	IAD 02	\N	MetroNet	300.0M x 20.0M	Primary	t	Mediacom Communications Corporation	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25461	IAF 01	\N	Fort Dodge Fiber	300.0M x 20.0M	Primary	t	Mediacom Communications Corporation	250.0M x 250.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25462	IAI 01	\N	Metronet	1000.0M x 30.0M	Primary	t	Mediacom Communications Corporation	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25463	IAN 01	\N	Mediacom	1000.0M x 30.0M	Primary	t	Cedar Falls	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25466	IAQ 01	\N	DSR Mediacom	300.0M x 20.0M	Primary	t	ComcastAgg CLink DSL	10.0 M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25467	IAQ 02	\N	Mediacom Communications Corporation	1000.0M x 30.0M	Primary	t	MetroNet	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25468	IAS 01	\N	MetroNet	300.0M x 30.0M	Primary	t	Sparklight	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25471	IDB 04	\N	EB2-CableOne Cable	500.0M x 500.0M	Primary	t	CenturyLink Fiber Plus	300.0M x 30.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25473	IDB 06	\N	Direct Communications	300.0M x 50.0M	Primary	t	EB2-CableOne Cable	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25478	ILC 02	\N	Comcast Workplace	750.0 M	Primary	t	Comcast Workplace	600.0M x 35.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25479	ILC 03	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25482	ILC 06	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25483	ILC 07	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 200.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25492	ILC 17	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25493	ILC 18	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25494	ILC 19	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25496	ILC 22	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25497	ILC 24	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25519	ILS 01	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25520	ILW 01	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25523	INC 02	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25530	INF 04	\N	GTT Ethernet	50.0M x 10.0M	Primary	t	EB2-Frontier Fiber	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25533	INI 02	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25535	INI 05	\N	ComcastAgg Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25539	INI 09	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25459	IAD 04	\N	Mediacom Communications Corporation	1000.0M x 30.0M	Primary	t	Metronet	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25537	INI 07	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T	25.0 M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25548	INL 01	\N	MetroNet	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25550	INW 01	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25554	KSK 01	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25564	KSW 01	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25568	KYE 01	\N	EB2-Windstream Fiber	250.0M x 25.0M	Primary	t	Comcast Workplace	200.0M x 200.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25569	KYL 01	\N	AT&T Broadband II	940.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26864	LAB 01	{Discount-Tire}	: Cox Business/BOI	300.0M x 30.0M	Primary	f	: REV Business	100.0M x 100.0M	Secondary	f	2025-07-07 11:46:54.544083	2025-07-07 10:54:59.444946	f	\N	\N	\N	\N	\N
26865	LAB 02	{Discount-Tire,Vision}	: Cox Business/BOI	300.0M x 30.0M	Primary	f	: AT&T Broadband II	300.0M x 300.0M	Secondary	f	2025-07-07 11:46:54.544083	2025-07-07 10:54:59.444946	f	\N	\N	\N	\N	\N
26866	LAB 03	{Discount-Tire,Vision}	: AT&T Broadband II	300.0M x 30.0M	Primary	f	: Cox Business/BOI	1000.0M x 1000.0M	Secondary	f	2025-07-07 11:46:54.544083	2025-07-07 10:54:59.444946	f	\N	\N	\N	\N	\N
26868	LAB 06	{Discount-Tire,Vision}	: AT&T Broadband II	1000.0M x 1000.0M	Primary	f	: Cox Business/BOI	300.0M x 30.0M	Secondary	f	2025-07-07 11:46:54.544083	2025-07-07 10:54:59.444946	f	\N	\N	\N	\N	\N
25580	MIB 01	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Comcast Workplace	1000.0M x 200.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25583	MID 05	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25585	MID 07	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25586	MID 09	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25590	MID 13	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25591	MID 14	\N	AT&T Broadband II	300.0 M	Primary	t	Comcast	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25592	MID 16	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25593	MID 17	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25594	MID 18	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25595	MID 19	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25623	MIL 15	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25668	MOK 07	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25676	MOS 01	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 200.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25697	NCC 03	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25705	NCC 11	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25708	NCC 15	\N	EB2-Windstream Fiber	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25713	NCC 20	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 200.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25720	NCC 28	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25731	NCC 43	\N	EB2-Windstream Fiber	600.0M x 35.0M	Primary	t	Spectrum	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25734	NCC 46	\N	Windstream	600.0M x 35.0M	Primary	t	Spectrum	100.0M x 100.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25741	NEG 01	\N	Allo Communications	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25743	NEO 01	\N	Great Plains Communications	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25744	NEO 03	\N	Great Plains Communications	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25745	NEO 04	\N	Great Plains Communications	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25748	NEO 07	\N	Great Plains Communications	300.0M x 30.0M	Primary	t	Cox Business/BOI	100.0M x 100.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25760	NMA 11	\N	Tularosa Basin Telephone Company	300.0M x 30.0M	Primary	t	TDS Cable	100.0M x 100.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25765	NMC 01	\N	Plateau Telecommunications	300.0M x 30.0M	Primary	t	Altice West	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25832	OHN 04	\N	Spectrum	400.0M x 400.0M	Primary	t	Windstream	600.0M x 35.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25836	OHS 02	\N	Altafiber	600.0M x 35.0M	Primary	t	Spectrum	600.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25847	OKO 04	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25849	OKO 06	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25855	OKO 12	\N	BluePeak Communications	300.0M x 75.0M	Primary	t	AT&T Broadband II	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25856	OKO 13	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25857	OKO 14	\N	AT&T Broadband II	500.0M x 50.0M	Primary	t	Vyve	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25860	OKT 02	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25861	OKT 03	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Cox Business/BOI	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25870	ORP 03	\N	Comcast	300.0 M	Primary	t	Ziply Fiber	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25876	ORP 10	\N	HiLight Internet	300.0M x 30.0M	Primary	t	Comcast Workplace	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25879	PAC 01	\N	Comcast Workplace	300.0M x 30.0M	Primary	t	Breezeline	300.0M x 30.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25891	SCC 02	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25904	SCC 15	\N	Farmers Telephone Cooperative, Inc.	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25906	SCC 17	\N	EB2-Frontier Fiber	600.0M x 35.0M	Primary	t	Spectrum	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25922	TNM 04	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25948	TXA 09	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25952	TXA 13	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25968	TXC 06	\N	AT&T Broadband II	500.0M x 50.0M	Primary	t	Altice	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25969	TXC 07	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25973	TXC 11	\N	Altice	500.0M x 50.0M	Primary	t	EB2-CableOne Cable	150.0M x 15.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25993	TXD 11	\N	AT&T Broadband II	940.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26001	TXD 22	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26004	TXD 26	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26015	TXD 38	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26017	TXD 40	\N	AT&T Broadband II	940.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26019	TXD 42	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26021	TXD 44	\N	AT&T Broadband II	940.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26022	TXD 45	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26027	TXD 51	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26033	TXD 58	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26086	TXH 05	\N	AT&T Broadband II	300.0 M	Primary	t	Comcast	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26087	TXH 10	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26107	TXH 33	\N	AT&T Broadband II	300.0M x 30.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26110	TXH 39	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26111	TXH 41	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26120	TXH 52	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26121	TXH 53	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26124	TXH 56	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26126	TXH 58	\N	Spectrum	600.0M x 35.0M	Primary	t	Comcast Workplace	600.0M x 35.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26128	TXH 60	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26129	TXH 61	\N	AT&T Broadband II	250.0M x 25.0M	Primary	t	Comcast Workplace	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26130	TXH 62	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26133	TXH 65	\N	AT&T Broadband II	1000.0 M	Primary	t	Comcast	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26134	TXH 66	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26137	TXH 69	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26140	TXH 72	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26144	TXH 77	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Comcast Workplace	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26148	TXH 81	\N	Metronet	15.0M x 3.0M	Primary	t	Rise Broadband	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26149	TXH 82	\N	Comcast	300.0 M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26198	TXS 24	\N	DSR AT&T	600.0M x 35.0M	Primary	t	Spectrum	600.0 M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26200	TXS 26	\N	GVTC Communications	600.0M x 35.0M	Primary	t	Spectrum	500.0M x 250.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26203	TXS 29	\N	AT&T Broadband II	300.0M x 20.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26204	TXS 30	\N	AT&T Broadband II	300.0M x 20.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26205	TXS 31	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26206	TXW 01	\N	AT&T Broadband II	500.0M x 50.0M	Primary	t	Altice	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26308	WIA 02	\N	AT&T Broadband II	600.0M x 35.0M	Primary	t	Spectrum	300.0M x 300.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26319	WIM 06	\N	AT&T Broadband II	940.0M x 35.0M	Primary	t	Spectrum	1000.0M x 200.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26320	WIO 01	\N	AT&T Broadband II	940.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
25140	AZY 02	\N	Allo Communications	600.0M x 35.0M	Primary	t	Spectrum	1000.0M x 1000.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26056	TXD 81	\N	EB2-Frontier Fiber	600.0M x 35.0M	Primary	t	Spectrum	500.0M x 500.0M	Secondary	t	2025-07-07 11:46:54.544083	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26049	TXD 74	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26050	TXD 75	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26052	TXD 77	\N	Spectrum	600.0M x 35.0M	Primary	t	EB2-Frontier Fiber	500.0M x 500.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26054	TXD 79	\N	Altice	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26058	TXD 83	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26063	TXD 88	\N	Altice West	500.0M x 50.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26064	TXD 89	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26151	TXH 84	\N	Comcast Workplace	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26160	TXH 93	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Comcast Workplace	300.0M x 30.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26180	TXS 05	\N	Spectrum	940.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26181	TXS 06	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26182	TXS 07	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26184	TXS 09	\N	AT&T Broadband II	1000.0M x 1000.0M	Primary	t	Spectrum	600.0M x 35.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
26195	TXS 21	\N	Spectrum	600.0M x 35.0M	Primary	t	AT&T Broadband II	300.0M x 300.0M	Secondary	t	2025-07-10 14:22:08.521283	2025-07-07 09:50:02.79366	f	\N	\N	\N	\N	\N
\.


--
-- Name: enriched_circuits_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.enriched_circuits_id_seq', 28985, true);


--
-- PostgreSQL database dump complete
--

