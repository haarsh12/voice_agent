// ============================================================
// schemes-catalogue.ts
// Complete catalogue of 45 Indian Government Schemes relevant to
// farmers, cooperatives, PACS, FPOs, SHGs and rural stakeholders.
// No external imports required.
// ============================================================

export type SchemeEntry = {
  slug: string
  short_name: string
  official_name: string
  scheme_type:
    | 'SCHEME'
    | 'INITIATIVE'
    | 'SERVICE'
    | 'POLICY'
    | 'PROGRAMME'
    | 'FUND'
    | 'INSURANCE'
    | 'FINANCIAL_PRODUCT'
  category: string
  subcategory: string
  ministry: string
  department: string
  implementing_authority: string
  description: string
  objective: string
  benefits: string
  eligibility: string
  application_process: string
  required_documents: string
  beneficiary_tags: Array<
    | 'Farmer'
    | 'PACS'
    | 'Cooperative'
    | 'FPO'
    | 'SHG'
    | 'Women'
    | 'Youth'
    | 'Entrepreneur'
    | 'Fisher'
    | 'Dairy Farmer'
    | 'Rural Household'
    | 'Livestock Farmer'
    | 'All Citizens'
  >
  relevant_user_types: Array<
    | 'farmer'
    | 'pacs_member'
    | 'cooperative_member'
    | 'cooperative_official'
    | 'rural_stakeholder'
    | 'other'
  >
  geographic_scope: 'NATIONAL' | 'STATE'
  applicable_states: string[]
  status: 'ACTIVE'
  official_url: string
  helpline: string | null
  launched_year: number | null
  budget_outlay: string | null
  tags: string[]
}

export const SCHEMES_CATALOGUE: SchemeEntry[] = [
  // ─────────────────────────────────────────────────────────
  // 1. PM-KISAN
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pm-kisan',
    short_name: 'PM-KISAN',
    official_name: 'Pradhan Mantri Kisan Samman Nidhi',
    scheme_type: 'SCHEME',
    category: 'Agriculture',
    subcategory: 'Farmer Income Support',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'Department of Agriculture & Farmers Welfare, State Governments',
    description:
      'PM-KISAN provides income support of ₹6,000 per year directly to small and marginal farmer families across India. The amount is transferred in three equal installments of ₹2,000 every four months directly into farmers\' bank accounts. This scheme aims to supplement farmers\' financial needs for procuring inputs and meeting household expenses.',
    objective:
      'To supplement the financial needs of Small and Marginal Farmers for procuring various inputs to ensure proper crop health and appropriate yields, commensurate with the anticipated farm income at the end of each crop cycle.',
    benefits:
      '₹6,000 per year direct bank transfer in three equal installments of ₹2,000 every four months.',
    eligibility:
      'All landholding farmers\' families (husband, wife and minor children) with cultivable agricultural land up to 2 hectares. Excludes institutional landholders, constitutional post-holders, serving/retired government employees, income-tax payers, and professionals like doctors, engineers, lawyers, CA, and architects.',
    application_process:
      'Farmers can self-register on the PM-KISAN portal (pmkisan.gov.in) or approach the nearest Common Service Centre (CSC), Patwari, or agriculture department office. Aadhaar-based verification is mandatory.',
    required_documents:
      'Aadhaar card, land ownership records (Khatoni/Jamabandi), bank account details (passbook), mobile number.',
    beneficiary_tags: ['Farmer', 'Rural Household'],
    relevant_user_types: ['farmer', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://pmkisan.gov.in',
    helpline: '155261',
    launched_year: 2019,
    budget_outlay: '₹60,000 crore per year',
    tags: ['income support', 'direct benefit transfer', 'small farmers', 'marginal farmers', 'DBT'],
  },

  // ─────────────────────────────────────────────────────────
  // 2. PMFBY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pmfby',
    short_name: 'PMFBY',
    official_name: 'Pradhan Mantri Fasal Bima Yojana',
    scheme_type: 'INSURANCE',
    category: 'Crop Insurance',
    subcategory: 'Crop Risk Coverage',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'Agriculture Insurance Company of India (AIC) and empanelled private insurance companies',
    description:
      'PMFBY is a crop insurance scheme that provides financial support to farmers suffering crop loss or damage due to unforeseen events such as natural calamities, pests, and diseases. Farmers pay a very low premium — 2% for Kharif, 1.5% for Rabi, and 5% for horticulture/commercial crops — and the remaining premium is shared between Central and State governments. The scheme uses modern technology like remote sensing and drones for quick and accurate crop loss assessment.',
    objective:
      'To provide financial support to farmers suffering crop loss/damage due to unforeseen calamities; to stabilise the income of farmers to ensure their continuance in farming; and to encourage farmers to adopt innovative agricultural practices.',
    benefits:
      'Full insured sum compensated on crop loss due to non-preventable risks. Low premium: 2% for Kharif, 1.5% for Rabi, 5% for horticulture crops. Post-harvest losses covered for up to 14 days. Localised calamities like hailstorm and landslide also covered.',
    eligibility:
      'All farmers growing notified crops in notified areas. Compulsory for loanee farmers (who have availed crop loans from financial institutions); voluntary for non-loanee farmers.',
    application_process:
      'Loanee farmers are automatically enrolled by banks. Non-loanee farmers can enrol through banks, insurance company agents, CSCs, or the PMFBY portal/app. Registration must be done before the cutoff date for each crop season.',
    required_documents:
      'Aadhaar card, bank account details, land records (7/12 or Khatoni), sowing certificate (for non-loanee farmers), mobile number.',
    beneficiary_tags: ['Farmer'],
    relevant_user_types: ['farmer'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://pmfby.gov.in',
    helpline: '14447',
    launched_year: 2016,
    budget_outlay: '₹15,000 crore per year (approximate)',
    tags: ['crop insurance', 'natural calamity', 'kharif', 'rabi', 'premium subsidy'],
  },

  // ─────────────────────────────────────────────────────────
  // 3. Kisan Credit Card
  // ─────────────────────────────────────────────────────────
  {
    slug: 'kisan-credit-card',
    short_name: 'KCC',
    official_name: 'Kisan Credit Card Scheme',
    scheme_type: 'FINANCIAL_PRODUCT',
    category: 'Agricultural Credit',
    subcategory: 'Short-term Credit',
    ministry: 'Ministry of Agriculture & Farmers Welfare / Reserve Bank of India / NABARD',
    department: 'Department of Financial Services / Department of Agriculture & Farmers Welfare',
    implementing_authority: 'Commercial Banks, Regional Rural Banks (RRBs), Cooperative Banks, NABARD',
    description:
      'The Kisan Credit Card (KCC) provides farmers with timely and adequate credit for their short-term agricultural needs, including purchase of inputs like seeds, fertilisers, and pesticides, as well as allied activities and non-farm expenses. The card operates like a revolving credit line with a flexible repayment schedule linked to harvesting and marketing seasons. Concessional interest rates apply through interest subvention, making it highly affordable for farmers.',
    objective:
      'To provide adequate and timely credit support from the banking system under a single window to farmers for their cultivation and other needs including purchase of inputs, post-harvest expenses, maintenance of farm assets, allied activities, and consumption needs.',
    benefits:
      'Revolving credit up to ₹3 lakh at concessional interest rate of 4% per annum (after interest subvention of 3% on timely repayment). Covers crop production, post-harvest, allied activities, and consumption needs. Personal accident insurance and asset insurance also covered.',
    eligibility:
      'All farmers — individual/joint borrowers who are owner cultivators. Tenant farmers, oral lessees, and sharecroppers. SHGs and Joint Liability Groups (JLGs) of farmers including tenant farmers.',
    application_process:
      'Apply at the nearest bank branch (commercial bank, RRB, or cooperative bank) with required documents. NABARD and PM-KISAN portal also facilitate KCC applications. Farmers with PM-KISAN registration can apply online.',
    required_documents:
      'Aadhaar card, PAN card, land records, passport-size photographs, bank account details, mobile number.',
    beneficiary_tags: ['Farmer', 'Rural Household'],
    relevant_user_types: ['farmer', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.nabard.org/content1.aspx?id=572',
    helpline: null,
    launched_year: 1998,
    budget_outlay: null,
    tags: ['credit card', 'agricultural loan', 'interest subvention', 'revolving credit', 'NABARD'],
  },

  // ─────────────────────────────────────────────────────────
  // 4. Agriculture Infrastructure Fund
  // ─────────────────────────────────────────────────────────
  {
    slug: 'agriculture-infrastructure-fund',
    short_name: 'AIF',
    official_name: 'Agriculture Infrastructure Fund',
    scheme_type: 'FUND',
    category: 'Agriculture Infrastructure',
    subcategory: 'Post-harvest Infrastructure',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'NABARD, Scheduled Commercial Banks, Cooperative Banks, NCDC',
    description:
      'The Agriculture Infrastructure Fund (AIF) is a medium to long-term debt financing facility for investment in viable projects for post-harvest management infrastructure and community farming assets. It offers interest subvention of 3% per annum and credit guarantee cover through CGTMSE for loans up to ₹2 crore. Eligible entities include farmers, FPOs, PACS, cooperatives, agri-entrepreneurs, and start-ups.',
    objective:
      'To provide a medium to long-term debt financing facility for investment in viable projects for post-harvest management infrastructure and community farming assets through interest subvention and financial support with credit guarantee.',
    benefits:
      'Interest subvention of 3% per annum for loans up to ₹2 crore. Credit guarantee coverage under CGTMSE for loans up to ₹2 crore. Moratorium of minimum 6 months and repayment period up to 7 years. Total fund corpus of ₹1,00,000 crore to be disbursed over 4 years.',
    eligibility:
      'Farmers, FPOs, PACS, Marketing Cooperative Societies, SHGs, Joint Liability Groups, Multipurpose Cooperative Societies, agri-entrepreneurs, start-ups, and Central/State government agencies.',
    application_process:
      'Apply online through the AIF portal (agriinfra.dac.gov.in) or through participating banks and financial institutions. Project proposal/DPR required. State-level monitoring committees oversee approvals.',
    required_documents:
      'Project report/DPR, entity registration documents, land ownership/lease documents, financial statements, Aadhaar/PAN of promoters.',
    beneficiary_tags: ['Farmer', 'PACS', 'Cooperative', 'FPO', 'SHG', 'Entrepreneur'],
    relevant_user_types: ['farmer', 'pacs_member', 'cooperative_member', 'cooperative_official', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://agriinfra.dac.gov.in',
    helpline: null,
    launched_year: 2020,
    budget_outlay: '₹1,00,000 crore',
    tags: ['post-harvest', 'cold storage', 'warehouse', 'interest subvention', 'agri infrastructure'],
  },

  // ─────────────────────────────────────────────────────────
  // 5. Computerization of PACS
  // ─────────────────────────────────────────────────────────
  {
    slug: 'computerization-of-pacs',
    short_name: 'Computerization of PACS',
    official_name: 'Computerization of Primary Agricultural Credit Societies (PACS)',
    scheme_type: 'INITIATIVE',
    category: 'Cooperative Development',
    subcategory: 'PACS Digitization',
    ministry: 'Ministry of Cooperation',
    department: 'Ministry of Cooperation',
    implementing_authority: 'NABARD, State Cooperative Banks, State Governments',
    description:
      'This initiative aims to computerize approximately 63,000 functional PACS across India to improve their operational efficiency, transparency, and accountability. A common national software is being developed and deployed to enable PACS to maintain digital records of all transactions, loans, and member data. Computerized PACS can also offer multiple services digitally to their members and integrate with national platforms.',
    objective:
      'To digitize all functional PACS by implementing a common accounting software to improve transparency, efficiency, and service delivery while integrating PACS with banking and government systems.',
    benefits:
      'Digital record-keeping for all PACS transactions. Integration with Core Banking Solutions (CBS) of District Central Cooperative Banks. Reduced paperwork and improved loan processing speed. Better audit and compliance. Access to multiple digital services for farmers.',
    eligibility:
      'All functional Primary Agricultural Credit Societies (PACS) across India.',
    application_process:
      'PACS are identified and enrolled by State Cooperative Departments and State Cooperative Banks. NABARD coordinates implementation and provides financial assistance to states.',
    required_documents:
      'PACS registration certificate, existing financial records, details of office-bearers.',
    beneficiary_tags: ['PACS', 'Cooperative', 'Farmer'],
    relevant_user_types: ['pacs_member', 'cooperative_official', 'cooperative_member'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mcs.gov.in',
    helpline: null,
    launched_year: 2022,
    budget_outlay: '₹2,516 crore',
    tags: ['PACS digitization', 'cooperative software', 'digital records', 'NABARD', 'cooperative reform'],
  },

  // ─────────────────────────────────────────────────────────
  // 6. Formation & Promotion of FPOs
  // ─────────────────────────────────────────────────────────
  {
    slug: 'formation-promotion-fpos',
    short_name: 'Formation & Promotion of FPOs',
    official_name: 'Formation and Promotion of Farmer Producer Organisations (FPOs)',
    scheme_type: 'SCHEME',
    category: 'Farmer Producer Organizations',
    subcategory: 'FPO Formation',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'SFAC, NABARD, State Governments, Implementing Agencies',
    description:
      'This scheme supports the formation and promotion of Farmer Producer Organisations (FPOs) to help small and marginal farmers aggregate their produce and collectively access better markets, technology, and credit. Each FPO is provided handholding support for 5 years through a Cluster-Based Business Organisation (CBBO). Financial assistance in the form of equity grants and credit guarantee is also provided to strengthen FPOs.',
    objective:
      'To ensure improved income of farmers by forming Farmer Producer Organisations (FPOs) that enable collective farming, processing, and marketing, with handholding support, equity grants, and credit guarantee.',
    benefits:
      'Equity grant of up to ₹15 lakh per FPO for matching equity mobilised. Credit guarantee up to ₹2 crore per FPO. Five years of professional handholding by CBBOs. Project Management Agency (PMA) support at state level.',
    eligibility:
      'Groups of farmers (minimum 300 farmers per FPO in plains, 100 in hilly/tribal areas). FPOs must be registered as Producer Companies, Cooperative Societies, or similar entities.',
    application_process:
      'Farmers form groups and approach Cluster-Based Business Organisations (CBBOs) for registration and handholding. State governments and implementing agencies like SFAC and NABARD facilitate the process.',
    required_documents:
      'Land records of member farmers, Aadhaar of members, entity registration documents, bank account details.',
    beneficiary_tags: ['Farmer', 'FPO', 'Rural Household'],
    relevant_user_types: ['farmer', 'cooperative_official', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://sfac.in',
    helpline: null,
    launched_year: 2020,
    budget_outlay: '₹6,865 crore',
    tags: ['FPO', 'farmer collective', 'equity grant', 'credit guarantee', 'SFAC'],
  },

  // ─────────────────────────────────────────────────────────
  // 7. New Multipurpose PACS
  // ─────────────────────────────────────────────────────────
  {
    slug: 'new-multipurpose-pacs',
    short_name: 'New Multipurpose PACS',
    official_name: 'Formation of New Multipurpose Primary Agricultural Credit Societies',
    scheme_type: 'INITIATIVE',
    category: 'Cooperative Development',
    subcategory: 'PACS Expansion',
    ministry: 'Ministry of Cooperation / NABARD',
    department: 'Ministry of Cooperation',
    implementing_authority: 'NABARD, State Cooperative Departments',
    description:
      'This initiative aims to set up new multipurpose PACS in approximately 2 lakh gram panchayats across India that currently do not have a PACS. The new PACS are designed to function as multipurpose entities offering not just credit but also services like insurance, CSC services, grain storage, and input supply. This expansion will extend the cooperative credit network to unserved rural areas.',
    objective:
      'To expand the PACS network to all gram panchayats of India, particularly those without any PACS, enabling cooperative services to reach every village.',
    benefits:
      'Creation of cooperative credit and service outlets in unserved panchayats. New PACS can offer 25+ business activities including banking correspondents, insurance, storage, CSC services, and input supply.',
    eligibility:
      'Farmer groups in gram panchayats/villages without an existing PACS. Minimum membership as per state cooperative laws.',
    application_process:
      'Facilitated by State Cooperative Departments and NABARD. Farmers in identified villages form groups, register under state cooperative acts, and receive support for operations.',
    required_documents:
      'Aadhaar of promoter members, land records, resolution of founding members, registration application as per state cooperative act.',
    beneficiary_tags: ['Farmer', 'PACS', 'Cooperative', 'Rural Household'],
    relevant_user_types: ['farmer', 'pacs_member', 'cooperative_official', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mcs.gov.in',
    helpline: null,
    launched_year: 2022,
    budget_outlay: null,
    tags: ['multipurpose PACS', 'new PACS', 'cooperative expansion', 'gram panchayat', 'rural cooperative'],
  },

  // ─────────────────────────────────────────────────────────
  // 8. New Dairy Cooperatives
  // ─────────────────────────────────────────────────────────
  {
    slug: 'new-dairy-cooperatives',
    short_name: 'New Dairy Cooperatives',
    official_name: 'Formation of New Dairy Cooperatives',
    scheme_type: 'INITIATIVE',
    category: 'Dairy & Animal Husbandry',
    subcategory: 'Dairy Cooperative Formation',
    ministry: 'Ministry of Cooperation / Ministry of Fisheries Animal Husbandry and Dairying',
    department: 'Ministry of Cooperation',
    implementing_authority: 'NDDB, State Dairy Federations, State Cooperative Departments',
    description:
      'This initiative promotes the formation of new dairy cooperatives in areas not covered by the existing dairy cooperative network, following the Amul model. It enables dairy farmers to collectively process and market milk, get better prices, and access veterinary and technical services. NDDB provides technical and financial support for establishing milk collection, chilling, and processing infrastructure.',
    objective:
      'To expand the dairy cooperative network across India, increase milk procurement from farmers, improve farmer incomes, and strengthen the rural dairy economy through cooperative institutions.',
    benefits:
      'Assured market for milk at remunerative prices. Access to veterinary services, artificial insemination, and animal feed. Collective bargaining power for dairy farmers. NDDB/government grants for infrastructure.',
    eligibility:
      'Dairy farmers in villages/areas not covered by existing dairy cooperatives. Minimum membership as per state cooperative laws.',
    application_process:
      'Farmers approach NDDB, State Dairy Federations, or State Cooperative Departments for facilitation. Formation follows the three-tier structure: Village Dairy Cooperative Society (VDCS) → District Milk Union → State Federation.',
    required_documents:
      'Aadhaar of member farmers, animal ownership records, resolution of founding members, registration documents.',
    beneficiary_tags: ['Dairy Farmer', 'Cooperative', 'Women', 'Rural Household'],
    relevant_user_types: ['farmer', 'cooperative_member', 'cooperative_official', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mcs.gov.in',
    helpline: null,
    launched_year: 2022,
    budget_outlay: null,
    tags: ['dairy cooperative', 'NDDB', 'milk procurement', 'Amul model', 'animal husbandry'],
  },

  // ─────────────────────────────────────────────────────────
  // 9. New Fishery Cooperatives
  // ─────────────────────────────────────────────────────────
  {
    slug: 'new-fishery-cooperatives',
    short_name: 'New Fishery Cooperatives',
    official_name: 'Formation of New Fishery Cooperatives',
    scheme_type: 'INITIATIVE',
    category: 'Fisheries',
    subcategory: 'Fishery Cooperative Formation',
    ministry: 'Ministry of Cooperation / Ministry of Fisheries Animal Husbandry and Dairying',
    department: 'Ministry of Cooperation',
    implementing_authority: 'NCDC, State Fisheries Departments, State Cooperative Departments',
    description:
      'This initiative promotes the establishment of new fishery cooperatives to organise fisher folk, improve their livelihoods, and provide access to credit, markets, and technical support. Fishery cooperatives help members collectively procure fishing inputs, market their catch, and access government welfare schemes. NCDC provides financial assistance and technical guidance for setting up fishery cooperative infrastructure.',
    objective:
      'To expand fishery cooperatives across India to strengthen the livelihoods of fishers and fish farmers, improve market access, and enable collective benefit from government schemes.',
    benefits:
      'Organised marketing of fish at better prices. Collective access to credit, gear, and inputs. NCDC financial assistance for infrastructure. Access to fisheries welfare schemes.',
    eligibility:
      'Fishers, fish farmers, and fish workers in areas without fishery cooperative coverage. Minimum membership as per applicable cooperative act.',
    application_process:
      'Fishers approach NCDC, State Fisheries Departments, or State Cooperative Departments for facilitation and registration support.',
    required_documents:
      'Aadhaar of member fishers, fishing licence/boat registration (if applicable), founding resolution, registration application.',
    beneficiary_tags: ['Fisher', 'Cooperative', 'Women', 'Rural Household'],
    relevant_user_types: ['cooperative_member', 'cooperative_official', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mcs.gov.in',
    helpline: null,
    launched_year: 2022,
    budget_outlay: null,
    tags: ['fishery cooperative', 'NCDC', 'fisher welfare', 'aquaculture', 'coastal livelihood'],
  },

  // ─────────────────────────────────────────────────────────
  // 10. Model Bye-Laws for PACS
  // ─────────────────────────────────────────────────────────
  {
    slug: 'model-bye-laws-pacs',
    short_name: 'Model Bye-Laws for PACS',
    official_name: 'Model Bye-Laws for Primary Agricultural Credit Societies (PACS)',
    scheme_type: 'POLICY',
    category: 'Cooperative Development',
    subcategory: 'PACS Governance',
    ministry: 'Ministry of Cooperation',
    department: 'Ministry of Cooperation',
    implementing_authority: 'Ministry of Cooperation, State Cooperative Departments',
    description:
      'The Ministry of Cooperation drafted and released new Model Bye-Laws for PACS in 2022 to enable them to function as multipurpose entities offering a wide range of services beyond agricultural credit. These bye-laws allow PACS to undertake over 25 business activities including retail sale of seeds and fertilisers, petrol pumps, gas agencies, banking correspondents, and CSC services. States are encouraged to adopt these model bye-laws to modernise their PACS.',
    objective:
      'To provide a modern governance framework for PACS that enables them to diversify into multiple business activities, improve financial viability, and serve as one-stop service centres for rural communities.',
    benefits:
      'PACS can legally undertake 25+ business activities. Improved governance and financial transparency. Empowers PACS to become financially viable and self-sustaining. Women and marginalised groups get representation.',
    eligibility:
      'All existing PACS that wish to adopt the new bye-laws and new PACS being formed.',
    application_process:
      'States adopt the Model Bye-Laws and notify them. Existing PACS hold special general body meetings to adopt the new bye-laws. New PACS register under the updated framework.',
    required_documents:
      'Existing PACS registration, general body resolution, application to Registrar of Cooperative Societies.',
    beneficiary_tags: ['PACS', 'Cooperative', 'Farmer'],
    relevant_user_types: ['pacs_member', 'cooperative_official'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mcs.gov.in',
    helpline: null,
    launched_year: 2022,
    budget_outlay: null,
    tags: ['PACS bye-laws', 'cooperative governance', 'multipurpose PACS', 'cooperative reform', 'model bye-laws'],
  },

  // ─────────────────────────────────────────────────────────
  // 11. PACS as CSC
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pacs-as-csc',
    short_name: 'PACS as CSC',
    official_name: 'PACS as Common Service Centres (CSC)',
    scheme_type: 'SERVICE',
    category: 'Cooperative Development',
    subcategory: 'Digital Service Delivery',
    ministry: 'Ministry of Cooperation / Ministry of Electronics & Information Technology',
    department: 'Ministry of Cooperation',
    implementing_authority: 'CSC e-Governance Services India Ltd (CSC SPV), NABARD, State Governments',
    description:
      'This initiative integrates PACS with the Common Service Centre (CSC) network to enable PACS to deliver government digital services to rural citizens at the village level. PACS functioning as CSCs can offer services like Aadhaar enrolment, banking correspondents, insurance, passport applications, bill payments, e-governance applications, and more. This adds a sustainable revenue stream for PACS while bringing digital services closer to farmers.',
    objective:
      'To leverage PACS as access points for e-governance and digital services in rural areas, generating additional income for PACS and making digital services available to farmers and rural citizens at their doorstep.',
    benefits:
      'PACS earn commission income from CSC services. Rural members get government and digital services locally. PACS become financially stronger. Digital financial services accessible to farmers.',
    eligibility:
      'Functional PACS that have been computerised and have the necessary infrastructure (computer, internet connectivity, operator).',
    application_process:
      'PACS apply through the CSC SPV portal or through NABARD and State Cooperative Departments. Upon approval, PACS are enrolled as CSC operators (Village Level Entrepreneurs).',
    required_documents:
      'PACS registration certificate, computerization proof, infrastructure details, bank account, operator Aadhaar.',
    beneficiary_tags: ['PACS', 'Cooperative', 'Farmer', 'Rural Household'],
    relevant_user_types: ['pacs_member', 'cooperative_official', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mcs.gov.in',
    helpline: null,
    launched_year: 2022,
    budget_outlay: null,
    tags: ['CSC', 'digital services', 'PACS revenue', 'e-governance', 'rural digital'],
  },

  // ─────────────────────────────────────────────────────────
  // 12. Grain Storage Plan
  // ─────────────────────────────────────────────────────────
  {
    slug: 'grain-storage-plan',
    short_name: 'Grain Storage Plan',
    official_name: 'World\'s Largest Grain Storage Plan in Cooperative Sector',
    scheme_type: 'PROGRAMME',
    category: 'Agriculture Infrastructure',
    subcategory: 'Storage Infrastructure',
    ministry: 'Ministry of Cooperation / Ministry of Consumer Affairs Food and Public Distribution',
    department: 'Ministry of Cooperation',
    implementing_authority: 'NABARD, FCI, CWC, NCDC, State Governments, PACS',
    description:
      'This ambitious programme aims to create decentralised grain storage capacity of 700 lakh metric tonnes through PACS across India, making it the world\'s largest grain storage initiative in the cooperative sector. PACS will be supported to construct warehouses and storage facilities on their premises using funds from multiple central schemes like RKVY, AIF, and NABARD. This will reduce post-harvest losses, enable direct procurement through PACS, and help farmers store and sell at better prices.',
    objective:
      'To create massive decentralised grain storage infrastructure at PACS level to reduce post-harvest losses, enable better price realisation for farmers, and strengthen food security.',
    benefits:
      'Massive increase in rural grain storage capacity. Reduced post-harvest losses for farmers. Farmers can store grain and sell at better prices. PACS earn income from warehousing charges.',
    eligibility:
      'PACS with land available for construction of warehouses and storage facilities.',
    application_process:
      'PACS apply through NABARD and State Cooperative Departments. Funding is provided through convergence of multiple schemes. District-level committees facilitate project approval.',
    required_documents:
      'PACS registration, land ownership documents, technical feasibility report, resolution of PACS general body.',
    beneficiary_tags: ['PACS', 'Cooperative', 'Farmer', 'Rural Household'],
    relevant_user_types: ['farmer', 'pacs_member', 'cooperative_official'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mcs.gov.in',
    helpline: null,
    launched_year: 2023,
    budget_outlay: null,
    tags: ['grain storage', 'warehouse', 'PACS infrastructure', 'post-harvest', 'food security'],
  },

  // ─────────────────────────────────────────────────────────
  // 13. PACS Jan Aushadhi Kendras
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pacs-jan-aushadhi-kendras',
    short_name: 'PACS Jan Aushadhi Kendras',
    official_name: 'Pradhan Mantri Bhartiya Janaushadhi Kendras through PACS',
    scheme_type: 'SERVICE',
    category: 'Cooperative Development',
    subcategory: 'Healthcare Services through PACS',
    ministry: 'Ministry of Cooperation / Ministry of Chemicals and Fertilizers',
    department: 'Ministry of Cooperation',
    implementing_authority: 'Bureau of Pharma PSUs of India (BPPI), PACS, State Cooperative Departments',
    description:
      'This initiative enables PACS to operate Pradhan Mantri Bhartiya Janaushadhi Kendras (PMBJK) — outlets selling generic medicines at very affordable prices — within their premises. Rural members and local communities can purchase quality generic medicines at up to 50–90% less than branded medicine prices. PACS earn a margin of 20% on sales, creating a sustainable additional income source.',
    objective:
      'To make affordable generic medicines available in rural areas through PACS and provide PACS with an additional income stream through operation of Jan Aushadhi Kendras.',
    benefits:
      'Rural community gets access to quality generic medicines at 50–90% lower prices. PACS earn 20% margin on sales. Over 1,900 medicines and 285 surgical items available at reduced prices.',
    eligibility:
      'PACS with infrastructure (space, computer, trained operator) willing to operate a PMBJK outlet.',
    application_process:
      'PACS apply through BPPI portal or through State Cooperative Departments. BPPI provides medicines on consignment basis or purchase. Training and support provided to outlet operator.',
    required_documents:
      'PACS registration, D.Pharm/B.Pharm certificate of operator or qualified pharmacist, space documents, bank account details.',
    beneficiary_tags: ['PACS', 'Cooperative', 'Rural Household', 'Farmer'],
    relevant_user_types: ['pacs_member', 'cooperative_official', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mcs.gov.in',
    helpline: null,
    launched_year: 2023,
    budget_outlay: null,
    tags: ['Jan Aushadhi', 'generic medicines', 'PACS services', 'healthcare', 'rural pharmacy'],
  },

  // ─────────────────────────────────────────────────────────
  // 14. PACS LPG Distributorship
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pacs-lpg-distributorship',
    short_name: 'PACS LPG Distributorship',
    official_name: 'LPG Distributorship through PACS',
    scheme_type: 'SERVICE',
    category: 'Cooperative Development',
    subcategory: 'Energy Distribution through PACS',
    ministry: 'Ministry of Cooperation / Ministry of Petroleum and Natural Gas',
    department: 'Ministry of Cooperation',
    implementing_authority: 'IOCL, BPCL, HPCL, PACS, State Cooperative Departments',
    description:
      'This initiative allows PACS to become authorised LPG distributors under oil marketing companies (IOC, BPCL, HPCL), enabling rural households to get cooking gas cylinders locally through PACS outlets. PACS earn a commission/margin on each cylinder distributed, creating a reliable revenue source while improving LPG access in rural areas. This aligns with PM Ujjwala Yojana beneficiaries getting easy refill access.',
    objective:
      'To improve LPG distribution and accessibility in rural areas through PACS and provide PACS with a sustainable income stream through the commission earned on LPG distribution.',
    benefits:
      'Rural members get LPG refills locally without travelling to town. PACS earn commission on each cylinder. Complements PM Ujjwala Yojana beneficiary network. Sustainable business activity for PACS.',
    eligibility:
      'PACS with adequate space for LPG cylinder storage, a designated go-down, and willingness to follow oil company guidelines.',
    application_process:
      'PACS apply to the nearest oil marketing company (IOCL/BPCL/HPCL) through the MoPNG/cooperative department nodal channel. PACS are given preference under the new policy.',
    required_documents:
      'PACS registration, land/storage space documents, fire safety NOC, bank account, operator ID proof.',
    beneficiary_tags: ['PACS', 'Cooperative', 'Rural Household', 'Women'],
    relevant_user_types: ['pacs_member', 'cooperative_official', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mcs.gov.in',
    helpline: null,
    launched_year: 2023,
    budget_outlay: null,
    tags: ['LPG', 'cooking gas', 'PACS revenue', 'rural energy', 'Ujjwala'],
  },

  // ─────────────────────────────────────────────────────────
  // 15. PACS Petrol/Diesel Dealership
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pacs-petrol-diesel-dealership',
    short_name: 'PACS Petrol/Diesel Dealership',
    official_name: 'Petrol/Diesel Retail Outlet Dealership through PACS',
    scheme_type: 'SERVICE',
    category: 'Cooperative Development',
    subcategory: 'Energy Distribution through PACS',
    ministry: 'Ministry of Cooperation / Ministry of Petroleum and Natural Gas',
    department: 'Ministry of Cooperation',
    implementing_authority: 'IOCL, BPCL, HPCL, PACS, State Cooperative Departments',
    description:
      'This initiative provides PACS the opportunity to operate petrol and diesel retail outlets (petrol pumps) in rural areas under oil marketing companies. PACS earn commission on fuel sales, making it one of the most lucrative additional business activities for well-located PACS. Farmers benefit from getting fuel for tractors and farm machinery locally without travelling long distances.',
    objective:
      'To improve fuel availability in rural areas through PACS retail outlets and provide PACS with a significant additional income source through fuel sales commission.',
    benefits:
      'Farmers get petrol and diesel for farm machinery locally. PACS earn commission on fuel sales — typically a significant income source. Reduces transportation cost and time for rural fuel access.',
    eligibility:
      'PACS with land on a national/state highway or in an area approved for a new retail outlet by oil marketing companies, with adequate financial capacity.',
    application_process:
      'PACS apply through oil marketing companies\' dealer selection portal or through Ministry of Cooperation/State Cooperative Departments. Selection based on location and criteria set by oil companies.',
    required_documents:
      'PACS registration, land documents, financial capacity proof, NOC from local authorities, operator ID.',
    beneficiary_tags: ['PACS', 'Cooperative', 'Farmer', 'Rural Household'],
    relevant_user_types: ['pacs_member', 'cooperative_official', 'rural_stakeholder', 'farmer'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mcs.gov.in',
    helpline: null,
    launched_year: 2023,
    budget_outlay: null,
    tags: ['petrol pump', 'fuel dealership', 'PACS revenue', 'rural fuel', 'farm machinery'],
  },

  // ─────────────────────────────────────────────────────────
  // 16. NCDC Cooperative Assistance
  // ─────────────────────────────────────────────────────────
  {
    slug: 'ncdc-cooperative-assistance',
    short_name: 'NCDC Cooperative Assistance',
    official_name: 'National Cooperative Development Corporation (NCDC) Financial Assistance Programmes',
    scheme_type: 'FUND',
    category: 'Cooperative Development',
    subcategory: 'Cooperative Finance',
    ministry: 'Ministry of Cooperation / NCDC',
    department: 'Ministry of Cooperation',
    implementing_authority: 'National Cooperative Development Corporation (NCDC)',
    description:
      'NCDC provides financial assistance in the form of loans, grants, and subsidies to cooperative societies across India for development of storage, processing, marketing, and other infrastructure. NCDC supports cooperatives across multiple sectors including agriculture, dairy, fisheries, consumer, housing, and labour. It also provides assistance for tribal cooperatives and women cooperatives with special terms.',
    objective:
      'To provide financial assistance to cooperative societies for planning, promoting, and developing programmes for production, processing, marketing, storage, export, and import of agricultural produce, food-stuffs, industrial goods, livestock, and other commodities.',
    benefits:
      'Loans at concessional rates for infrastructure development. Grants for capacity building and weaker section cooperatives. Special terms for tribal and women cooperatives. Support for cooperative education and training.',
    eligibility:
      'Cooperative societies registered under state cooperative acts, multi-state cooperative societies, and apex/district cooperative organisations.',
    application_process:
      'Cooperatives submit project proposals to NCDC directly or through State Governments. NCDC evaluates proposals and sanctions financial assistance. Disbursement through state government or directly.',
    required_documents:
      'Cooperative registration, audited financial statements, project report/DPR, resolution of managing committee, state government recommendation (for some schemes).',
    beneficiary_tags: ['Cooperative', 'PACS', 'Farmer', 'Women', 'Fisher', 'Dairy Farmer'],
    relevant_user_types: ['cooperative_member', 'cooperative_official', 'pacs_member'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.ncdc.in',
    helpline: null,
    launched_year: 1963,
    budget_outlay: null,
    tags: ['NCDC', 'cooperative loan', 'cooperative grant', 'cooperative infrastructure', 'NCDC assistance'],
  },

  // ─────────────────────────────────────────────────────────
  // 17. SMAM
  // ─────────────────────────────────────────────────────────
  {
    slug: 'smam',
    short_name: 'SMAM',
    official_name: 'Sub-Mission on Agricultural Mechanization (SMAM)',
    scheme_type: 'SCHEME',
    category: 'Agriculture',
    subcategory: 'Farm Mechanization',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'State Governments, Agriculture Departments',
    description:
      'SMAM promotes farm mechanization in India by providing financial assistance (subsidy) to farmers for purchase of agricultural machinery and equipment. It also supports establishment of Custom Hiring Centres (CHCs) and hi-tech hubs so that small and marginal farmers who cannot afford machinery can hire them at reasonable rates. The scheme also focuses on demonstration of new farm technologies and training of farmers.',
    objective:
      'To increase the reach of farm mechanization to small and marginal farmers and to the regions where farm power availability is low, by promoting custom hiring centres and providing subsidies on farm machinery purchase.',
    benefits:
      'Subsidy of 40–50% on purchase of agricultural machinery for individual farmers. Higher subsidy (up to 80%) for SC/ST and women farmers. Establishment of Custom Hiring Centres with 40% subsidy. Hi-tech hubs with 40% subsidy.',
    eligibility:
      'All categories of farmers. Priority to small and marginal farmers, SC/ST farmers, women farmers, and NE state farmers. Custom Hiring Centres can be set up by FPOs, cooperatives, and entrepreneurs.',
    application_process:
      'Apply through the agriculture department at district level or through the SMAM portal (agrimachinery.nic.in). Subsidies are directly transferred to beneficiary accounts or adjusted at dealer point.',
    required_documents:
      'Aadhaar card, land records, caste certificate (if applicable), bank account details, machinery purchase invoice.',
    beneficiary_tags: ['Farmer', 'FPO', 'Cooperative', 'Women', 'Entrepreneur'],
    relevant_user_types: ['farmer', 'cooperative_member', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://agrimachinery.nic.in',
    helpline: null,
    launched_year: 2014,
    budget_outlay: '₹3,250 crore (approx, across plan periods)',
    tags: ['farm machinery', 'mechanization', 'custom hiring', 'subsidy', 'tractor'],
  },

  // ─────────────────────────────────────────────────────────
  // 18. MIDH
  // ─────────────────────────────────────────────────────────
  {
    slug: 'midh',
    short_name: 'MIDH',
    official_name: 'Mission for Integrated Development of Horticulture (MIDH)',
    scheme_type: 'SCHEME',
    category: 'Horticulture',
    subcategory: 'Horticulture Development',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'National Horticulture Board (NHB), Coconut Development Board, State Horticulture Departments',
    description:
      'MIDH is a centrally sponsored scheme for holistic development of horticulture, covering fruits, vegetables, flowers, spices, mushrooms, and plantation crops. It provides financial assistance for area expansion, rejuvenation of old orchards, protected cultivation (poly-houses), post-harvest management, and market infrastructure. The scheme is implemented through multiple verticals including National Horticulture Mission (NHM), NHB, CDB, and NCPAH.',
    objective:
      'To promote holistic growth of the horticulture sector covering production, post-production management, and processing with the involvement of all stakeholders.',
    benefits:
      'Subsidy of 25–50% on establishment of horticulture farms. 50% subsidy on protected cultivation structures (poly-houses, shade nets). Support for cold storage, pack houses, and primary processing units. Training and capacity building.',
    eligibility:
      'Individual farmers, farmer groups, FPOs, cooperatives, SHGs, entrepreneurs. Specific eligibility criteria vary by component.',
    application_process:
      'Apply to the State Horticulture Department or District Horticulture Officer with project proposal. Online applications through state portals. Funds released to state governments who implement through districts.',
    required_documents:
      'Aadhaar, land records, bank account details, project proposal, photographs of land.',
    beneficiary_tags: ['Farmer', 'FPO', 'Cooperative', 'Women', 'Entrepreneur'],
    relevant_user_types: ['farmer', 'cooperative_member', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://midh.gov.in',
    helpline: null,
    launched_year: 2014,
    budget_outlay: '₹2,600 crore per year (approx)',
    tags: ['horticulture', 'fruits', 'vegetables', 'protected cultivation', 'NHM'],
  },

  // ─────────────────────────────────────────────────────────
  // 19. RKVY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'rkvy',
    short_name: 'RKVY',
    official_name: 'Rashtriya Krishi Vikas Yojana (RKVY)',
    scheme_type: 'SCHEME',
    category: 'Agriculture',
    subcategory: 'Agricultural Development',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'State Governments, State Agriculture Departments',
    description:
      'RKVY is a flagship scheme that provides states with flexible funds to boost agricultural growth and investment. States can use RKVY funds for any agricultural development activity including infrastructure, technology adoption, value chains, and agri-startups (under RAFTAAR component). The scheme also includes a dedicated RKVY-RAFTAAR sub-scheme to support agri-startups and innovation.',
    objective:
      'To incentivise states to increase public investment in agriculture and allied sectors, to achieve sustainable development and remunerative returns to farmers.',
    benefits:
      'Flexible block grants to states for agriculture development. Support for agri-startups through RAFTAAR (grants up to ₹25 lakh per startup). Funding for value chain development, agricultural infrastructure, and technology.',
    eligibility:
      'State governments for main RKVY. Agri-entrepreneurs and startups under RAFTAAR component. Farmers and farmer groups for specific sub-activities.',
    application_process:
      'States prepare Strategic Research and Extension Plans and submit to centre. Under RAFTAAR, startups apply through RKVY portal. Individual farmer activities applied through state agriculture departments.',
    required_documents:
      'Varies by activity. Typically includes identity proof, land records, project proposal, and financial statements for startups.',
    beneficiary_tags: ['Farmer', 'Entrepreneur', 'FPO', 'Cooperative'],
    relevant_user_types: ['farmer', 'rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://rkvy.nic.in',
    helpline: null,
    launched_year: 2007,
    budget_outlay: '₹10,433 crore (2021–22 to 2025–26)',
    tags: ['agricultural development', 'state grants', 'agri startup', 'RAFTAAR', 'rural investment'],
  },

  // ─────────────────────────────────────────────────────────
  // 20. PKVY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pkvy',
    short_name: 'PKVY',
    official_name: 'Paramparagat Krishi Vikas Yojana (PKVY)',
    scheme_type: 'SCHEME',
    category: 'Organic Farming',
    subcategory: 'Organic Farming Promotion',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'National Centre of Organic and Natural Farming (NCOF), State Agriculture Departments',
    description:
      'PKVY promotes organic farming in India through a cluster approach where farmers form groups of at least 50 acres and collectively adopt organic farming practices. The scheme provides financial support for conversion to organic farming, procurement of bio-inputs, training, and certification under the Participatory Guarantee System (PGS-India). Certified organic produce fetches premium prices in domestic and export markets.',
    objective:
      'To promote organic farming in India through cluster approach and PGS certification, improve soil health, and provide premium market access to organic produce.',
    benefits:
      'Financial support of ₹50,000 per hectare over 3 years for conversion to organic farming. Assistance for bio-inputs, capacity building, certification, and market linkages. PGS certification at no cost to farmers.',
    eligibility:
      'Farmers willing to adopt organic farming. Minimum cluster of 50 acres (20 hectares) with at least 20 farmers per cluster.',
    application_process:
      'Farmers form clusters and approach state agriculture departments or NCOF. States implement through district agriculture offices. Clusters are registered and supported over 3 years.',
    required_documents:
      'Aadhaar, land records, group formation documents, soil health card, bank account details.',
    beneficiary_tags: ['Farmer', 'SHG', 'Rural Household'],
    relevant_user_types: ['farmer', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://pgsindia-ncof.gov.in',
    helpline: null,
    launched_year: 2015,
    budget_outlay: '₹2,500 crore (approx over 5 years)',
    tags: ['organic farming', 'PGS certification', 'bio-inputs', 'sustainable agriculture', 'cluster farming'],
  },

  // ─────────────────────────────────────────────────────────
  // 21. Natural Farming Mission
  // ─────────────────────────────────────────────────────────
  {
    slug: 'natural-farming-mission',
    short_name: 'Natural Farming Mission',
    official_name: 'National Mission on Natural Farming',
    scheme_type: 'INITIATIVE',
    category: 'Organic Farming',
    subcategory: 'Natural Farming',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'National Centre of Organic and Natural Farming (NCOF), State Agriculture Departments',
    description:
      'The National Mission on Natural Farming promotes zero-budget natural farming (ZBNF) and agro-ecology based farming practices that minimize or eliminate chemical inputs. The mission provides farmers with training, technical support, and assistance for Beejamrit, Jeevamrit, and other natural farming preparations. It aims to reduce input costs significantly while maintaining or improving yields and soil health.',
    objective:
      'To mainstream natural farming across India, reducing input costs for farmers, improving soil health, protecting the environment, and providing consumers with chemical-free food.',
    benefits:
      'Significant reduction in farming input costs (potentially zero external input cost). Training on natural farming techniques (Beejamrit, Jeevamrit, etc.). Financial support for conversion and model farms. Improved soil health and biodiversity.',
    eligibility:
      'All farmers willing to adopt natural farming practices. Preference for small and marginal farmers.',
    application_process:
      'Farmers enrol through state agriculture departments. Training camps and demonstrations are organised. Farmers can also visit Krishi Vigyan Kendras for guidance.',
    required_documents:
      'Aadhaar, land records, bank account details.',
    beneficiary_tags: ['Farmer', 'Rural Household', 'Women'],
    relevant_user_types: ['farmer', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://naturalfarming.dac.gov.in',
    helpline: null,
    launched_year: 2023,
    budget_outlay: '₹2,481 crore (2023–24 to 2025–26)',
    tags: ['natural farming', 'zero budget farming', 'ZBNF', 'jeevamrit', 'chemical-free'],
  },

  // ─────────────────────────────────────────────────────────
  // 22. Soil Health Card
  // ─────────────────────────────────────────────────────────
  {
    slug: 'soil-health-card',
    short_name: 'Soil Health Card',
    official_name: 'Soil Health Card (SHC) Scheme',
    scheme_type: 'SCHEME',
    category: 'Soil Health',
    subcategory: 'Soil Testing',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'State Agriculture Departments, Soil Testing Laboratories',
    description:
      'The Soil Health Card scheme provides farmers with a card that contains information about the nutrient status of their soil along with crop-wise recommendations for fertilizer dosage. Soil samples are collected from farmers\' fields and tested in soil testing laboratories, and results along with recommendations are printed on the card. This helps farmers apply the right amount and type of fertilizers, reducing cost and improving productivity.',
    objective:
      'To provide every farmer with soil nutrient status of their holdings and advise on appropriate dosage of nutrients to improve farm productivity and reduce input cost.',
    benefits:
      'Free soil testing for farmers every 2 years. Personalized crop-wise fertilizer recommendation. Helps reduce fertilizer expenditure and improve yield. Digital SHC available online.',
    eligibility:
      'All farmers across India. Soil samples collected from every 2.5 hectares in irrigated areas and every 10 hectares in rain-fed areas.',
    application_process:
      'Farmers contact local agriculture officers or Krishi Vigyan Kendras. Soil samples are collected by government personnel from farmers\' fields. Results and recommendations are provided on the SHC card.',
    required_documents:
      'Aadhaar card, land records, mobile number.',
    beneficiary_tags: ['Farmer', 'Rural Household'],
    relevant_user_types: ['farmer', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://soilhealth.dac.gov.in',
    helpline: null,
    launched_year: 2015,
    budget_outlay: '₹568 crore (approx per cycle)',
    tags: ['soil testing', 'fertilizer recommendation', 'soil nutrients', 'soil health', 'precision farming'],
  },

  // ─────────────────────────────────────────────────────────
  // 23. PMKSY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pmksy',
    short_name: 'PMKSY',
    official_name: 'Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)',
    scheme_type: 'SCHEME',
    category: 'Irrigation',
    subcategory: 'Irrigation Coverage',
    ministry: 'Ministry of Jal Shakti / Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Water Resources, RD & GR / Dept of Agriculture & Farmers Welfare',
    implementing_authority: 'State Governments, NABARD, Departments of Water Resources and Agriculture',
    description:
      'PMKSY aims to achieve "Har Khet Ko Pani" (water to every field) and "More Crop per Drop" by expanding irrigation coverage and improving water use efficiency. The scheme has multiple components: AIBP (Accelerated Irrigation Benefits Programme), PMKSY-HKKP (Har Khet Ko Pani), and PMKSY-WDC (Watershed Development Component). It promotes micro-irrigation technologies like drip and sprinkler systems with subsidies.',
    objective:
      'To ensure access to protective irrigation to all agricultural farms and improve water use efficiency through micro-irrigation and watershed development.',
    benefits:
      'Subsidy of 45–55% on drip and sprinkler irrigation systems (55% for small/marginal farmers). Expansion of irrigation coverage. Completion of stalled irrigation projects under AIBP. Improved water use efficiency.',
    eligibility:
      'All farmers for micro-irrigation components. State governments for major irrigation project components. Farmers in command areas of completed irrigation projects.',
    application_process:
      'Apply for micro-irrigation subsidy through state agriculture/horticulture departments. District-level agriculture officers process applications. Watershed development applications through state rural development departments.',
    required_documents:
      'Aadhaar, land records, bank account details, soil and water source details for micro-irrigation.',
    beneficiary_tags: ['Farmer', 'Rural Household'],
    relevant_user_types: ['farmer', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://pmksy.gov.in',
    helpline: null,
    launched_year: 2015,
    budget_outlay: '₹93,068 crore (2021–26)',
    tags: ['irrigation', 'drip irrigation', 'sprinkler', 'water efficiency', 'Har Khet Ko Pani'],
  },

  // ─────────────────────────────────────────────────────────
  // 24. e-NAM
  // ─────────────────────────────────────────────────────────
  {
    slug: 'e-nam',
    short_name: 'e-NAM',
    official_name: 'National Agriculture Market (e-NAM)',
    scheme_type: 'SERVICE',
    category: 'Agricultural Marketing',
    subcategory: 'Online Mandi Platform',
    ministry: 'Ministry of Agriculture & Farmers Welfare / SFAC',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'Small Farmers Agri-Business Consortium (SFAC), State APMC Boards',
    description:
      'e-NAM is a pan-India electronic trading portal that networks existing APMC mandis to create a unified national market for agricultural commodities. Farmers can register and sell their produce through e-NAM and get competitive prices through online transparent bidding by traders from across the country. The platform enables farmers to check commodity arrivals, prices, and buyer information digitally.',
    objective:
      'To create a unified national market for agricultural commodities by networking APMCs across India to promote transparent price discovery and better marketing for farmers.',
    benefits:
      'Transparent online auction process providing competitive prices to farmers. Real-time price information for 200+ commodities. Reduced market fees and intermediaries. Access to buyers from across India. Integrated with quality testing and logistics.',
    eligibility:
      'All farmers whose APMC mandi is connected to e-NAM platform. Farmers can register on the e-NAM portal or mobile app.',
    application_process:
      'Farmers register on enam.gov.in or mobile app with Aadhaar and bank details. After registration, farmers can sell produce at e-NAM connected mandis and participate in online auctions.',
    required_documents:
      'Aadhaar card, bank account details, land records (optional), mobile number.',
    beneficiary_tags: ['Farmer', 'FPO', 'Cooperative'],
    relevant_user_types: ['farmer', 'cooperative_member', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.enam.gov.in',
    helpline: '1800-270-0224',
    launched_year: 2016,
    budget_outlay: null,
    tags: ['e-NAM', 'online mandi', 'agricultural marketing', 'price discovery', 'APMC'],
  },

  // ─────────────────────────────────────────────────────────
  // 25. FPO Scheme (10,000 FPOs)
  // ─────────────────────────────────────────────────────────
  {
    slug: 'fpo-scheme',
    short_name: 'FPO Scheme (10,000 FPOs)',
    official_name: 'Formation and Promotion of 10,000 Farmer Producer Organisations (FPOs)',
    scheme_type: 'SCHEME',
    category: 'Farmer Producer Organizations',
    subcategory: 'FPO Support',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'SFAC, NABARD, NCDC, State Governments',
    description:
      'The government has a central scheme to form 10,000 new FPOs over 5 years (2020–25) to strengthen farmer collectives. Each FPO receives handholding support for 5 years, equity grant of up to ₹15 lakh, and credit guarantee coverage. The scheme targets one FPO per cluster of 100–500 farmers and focuses on commodity/produce specialisation for better market integration.',
    objective:
      'To promote and strengthen 10,000 new FPOs across India to give collective bargaining power to farmers, improve market linkages, technology access, and credit for small and marginal farmers.',
    benefits:
      'Equity grant of up to ₹15 lakh per FPO. Credit guarantee coverage up to ₹2 crore. 5 years professional handholding by CBBOs. Exposure visits, capacity building, and market linkage support.',
    eligibility:
      'Groups of at least 300 farmers in plain areas (100 in hilly/tribal areas) who register or want to register as an FPO (Producer Company, Multi-State Cooperative, etc.).',
    application_process:
      'Farmers form groups in identified clusters and approach CBBOs assigned by implementing agencies. CBBOs help in FPO registration and guide in business planning and market linkages.',
    required_documents:
      'Aadhaar and land records of member farmers, resolution of founding members, FPO registration documents, bank account details.',
    beneficiary_tags: ['Farmer', 'FPO', 'Women', 'Rural Household'],
    relevant_user_types: ['farmer', 'cooperative_official', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://sfac.in/schemes-fpo.aspx',
    helpline: null,
    launched_year: 2020,
    budget_outlay: '₹6,865 crore (2020–25)',
    tags: ['FPO', '10000 FPOs', 'farmer collective', 'CBBO', 'producer company'],
  },

  // ─────────────────────────────────────────────────────────
  // 26. PM-KMY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pm-kmy',
    short_name: 'PM-KMY',
    official_name: 'Pradhan Mantri Kisan Maandhan Yojana (PM-KMY)',
    scheme_type: 'SCHEME',
    category: 'Social Security',
    subcategory: 'Farmer Pension',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    department: 'Department of Agriculture & Farmers Welfare',
    implementing_authority: 'Life Insurance Corporation (LIC), Common Service Centres (CSC)',
    description:
      'PM-KMY is a voluntary and contributory pension scheme for small and marginal farmers aged 18 to 40 years. After contributing a monthly amount ranging from ₹55 to ₹200 (matching government contribution), enrolled farmers receive a minimum assured pension of ₹3,000 per month upon reaching age 60. This scheme provides social security to small farmers in their old age.',
    objective:
      'To provide social security and pension to small and marginal farmers in their old age, ensuring a minimum income after retirement from farming.',
    benefits:
      'Minimum assured pension of ₹3,000 per month after age 60. Government contributes equal amount to the pension fund. If subscriber dies, spouse gets 50% family pension. Premium waived for farmers already receiving PM-KISAN benefit (deducted from PM-KISAN amount).',
    eligibility:
      'Small and marginal farmers (cultivable land up to 2 hectares) aged 18 to 40 years. Must not be covered under any other government pension scheme or EPFO/ESIC.',
    application_process:
      'Enrol at nearest CSC or PM-KISAN portal with Aadhaar and bank details. Monthly contributions deducted from linked savings account or PM-KISAN installment.',
    required_documents:
      'Aadhaar card, bank account details (savings bank account), land records, mobile number.',
    beneficiary_tags: ['Farmer', 'Rural Household'],
    relevant_user_types: ['farmer', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://maandhan.in/shramyogi',
    helpline: '1800-267-6888',
    launched_year: 2019,
    budget_outlay: null,
    tags: ['farmer pension', 'social security', 'PM-KMY', 'old age', 'retirement'],
  },

  // ─────────────────────────────────────────────────────────
  // 27. PMEGP
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pmegp',
    short_name: 'PMEGP',
    official_name: 'Prime Minister\'s Employment Generation Programme (PMEGP)',
    scheme_type: 'SCHEME',
    category: 'Entrepreneurship & Employment',
    subcategory: 'Micro Enterprise Creation',
    ministry: 'Ministry of Micro, Small and Medium Enterprises (MSME) / KVIC',
    department: 'Ministry of MSME',
    implementing_authority: 'Khadi and Village Industries Commission (KVIC), KVIB, DIC',
    description:
      'PMEGP is a credit-linked subsidy scheme that helps individuals and groups set up new micro-enterprises in manufacturing and service sectors. The government provides a margin money (subsidy) of 15–35% of the project cost, and the rest is financed by bank loans. PMEGP targets unemployed youth, artisans, and rural entrepreneurs and aims to generate self-employment through micro-enterprises.',
    objective:
      'To generate employment opportunities in rural as well as urban areas through establishment of micro-enterprises by helping unemployed youth and traditional artisans set up new businesses.',
    benefits:
      'Margin money (subsidy) of 25% for urban and 35% for rural areas (higher for SC/ST/women/minorities/physically handicapped/ex-servicemen). Maximum project cost: ₹25 lakh (manufacturing), ₹10 lakh (service). No collateral for loans up to ₹10 lakh.',
    eligibility:
      'Any individual above 18 years of age. For projects above ₹10 lakh (manufacturing) and ₹5 lakh (business/service), VIII Standard pass. SHGs, charitable trusts, registered institutions, cooperative societies also eligible.',
    application_process:
      'Apply online through KVIC portal (kviconline.gov.in/pmegpeportal) or through District Industries Centre (DIC), KVIC, or KVIB offices. Application followed by training and bank loan application.',
    required_documents:
      'Aadhaar, PAN card, educational qualification certificate, caste certificate (if applicable), business plan, bank account details.',
    beneficiary_tags: ['Entrepreneur', 'Youth', 'Women', 'Rural Household', 'SHG'],
    relevant_user_types: ['rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://kviconline.gov.in/pmegpeportal',
    helpline: null,
    launched_year: 2008,
    budget_outlay: '₹13,554 crore (2021–22 to 2025–26)',
    tags: ['entrepreneurship', 'self-employment', 'KVIC', 'micro enterprise', 'subsidy'],
  },

  // ─────────────────────────────────────────────────────────
  // 28. PMFME
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pmfme',
    short_name: 'PMFME',
    official_name: 'Pradhan Mantri Formalisation of Micro Food Processing Enterprises (PMFME) Scheme',
    scheme_type: 'SCHEME',
    category: 'Food Processing',
    subcategory: 'Micro Food Enterprise',
    ministry: 'Ministry of Food Processing Industries',
    department: 'Ministry of Food Processing Industries',
    implementing_authority: 'Ministry of Food Processing Industries, State Governments, NABARD',
    description:
      'PMFME supports existing micro food processing enterprises to formalize, scale up, and become competitive. Individual micro enterprises get 35% credit-linked capital subsidy (up to ₹10 lakh) for upgrading processing equipment. FPOs, cooperatives, and SHGs get capital subsidy for common infrastructure. The scheme also provides branding and marketing support, and seed capital to SHG members for working capital and small tools.',
    objective:
      'To enhance the competitiveness of existing individual micro-enterprises and promote formalization of the sector, support FPOs, SHGs, and cooperatives in food processing, and create better infrastructure for micro food processing.',
    benefits:
      'Credit-linked capital subsidy of 35% (up to ₹10 lakh) for individual micro enterprises. Seed capital of ₹40,000 for SHG members. Common infrastructure support for FPOs/cooperatives/SHGs. Branding and marketing support.',
    eligibility:
      'Existing micro food processing enterprises (turnover under ₹1 crore, employees under 10). SHGs, FPOs, cooperatives for common infrastructure. Preference for SC/ST/women entrepreneurs and Aspirational Districts.',
    application_process:
      'Apply online through the PMFME portal (pmfme.mofpi.gov.in) or through state nodal agencies. District Resource Persons (DRPs) assist in application and DPR preparation.',
    required_documents:
      'Aadhaar, business registration/UDYAM, bank account, project report, machinery quotations, existing enterprise documents.',
    beneficiary_tags: ['Entrepreneur', 'Women', 'SHG', 'FPO', 'Cooperative', 'Rural Household'],
    relevant_user_types: ['rural_stakeholder', 'cooperative_member', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://pmfme.mofpi.gov.in',
    helpline: null,
    launched_year: 2020,
    budget_outlay: '₹10,000 crore (2020–21 to 2024–25)',
    tags: ['food processing', 'micro enterprise', 'capital subsidy', 'SHG', 'ODOP'],
  },

  // ─────────────────────────────────────────────────────────
  // 29. PMMY / MUDRA
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pmmy-mudra',
    short_name: 'PMMY / MUDRA',
    official_name: 'Pradhan Mantri Mudra Yojana (PMMY)',
    scheme_type: 'FINANCIAL_PRODUCT',
    category: 'Financial Inclusion',
    subcategory: 'Micro Enterprise Loans',
    ministry: 'Ministry of Finance / Micro Units Development and Refinance Agency (MUDRA)',
    department: 'Department of Financial Services',
    implementing_authority: 'Micro Units Development and Refinance Agency (MUDRA), Banks, MFIs, NBFCs',
    description:
      'PMMY / MUDRA provides loans to non-corporate, non-farm small and micro enterprises (MSME) through its three lending categories: Shishu (up to ₹50,000), Kishore (₹50,001–₹5 lakh), and Tarun (₹5 lakh–₹10 lakh). These collateral-free loans support micro-entrepreneurs in setting up or expanding their businesses. MUDRA refinances banks and MFIs that lend to micro-enterprises under the scheme.',
    objective:
      'To provide affordable credit to small and micro entrepreneurs to set up or expand non-farm income-generating micro-enterprises and support financial inclusion.',
    benefits:
      'Collateral-free loans up to ₹10 lakh. Three tiers: Shishu (up to ₹50,000), Kishore (up to ₹5 lakh), Tarun (up to ₹10 lakh). Competitive interest rates. MUDRA card for working capital. No processing fee for Shishu loans.',
    eligibility:
      'Any Indian citizen with a business plan for non-farm income generating activity in manufacturing, trading, or services sector. Individuals, proprietorships, partnerships, and other entities.',
    application_process:
      'Apply at nearest bank, NBFC, MFI, or through Udyamimitra portal (udyamimitra.in). Application along with business plan and documents submitted to lending institution.',
    required_documents:
      'Aadhaar, PAN, residential proof, photographs, business plan, bank statements, relevant business documents.',
    beneficiary_tags: ['Entrepreneur', 'Women', 'Youth', 'Rural Household'],
    relevant_user_types: ['rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.mudra.org.in',
    helpline: '1800-180-1111',
    launched_year: 2015,
    budget_outlay: null,
    tags: ['MUDRA loan', 'micro enterprise', 'Shishu', 'Kishore', 'Tarun'],
  },

  // ─────────────────────────────────────────────────────────
  // 30. PMJDY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pmjdy',
    short_name: 'PMJDY',
    official_name: 'Pradhan Mantri Jan Dhan Yojana (PMJDY)',
    scheme_type: 'SCHEME',
    category: 'Financial Inclusion',
    subcategory: 'Banking Access',
    ministry: 'Ministry of Finance / Department of Financial Services',
    department: 'Department of Financial Services',
    implementing_authority: 'All Scheduled Commercial Banks, RRBs, Cooperative Banks',
    description:
      'PMJDY aims to ensure universal access to banking, savings, remittance, insurance, and pension services for all citizens, especially the unbanked population. Account holders get a zero-balance savings account, a RuPay debit card, ₹1 lakh accident insurance cover, ₹30,000 life insurance cover, and access to overdraft facility of up to ₹10,000 after satisfactory account conduct for 6 months.',
    objective:
      'To ensure comprehensive financial inclusion by providing universal access to banking facilities with at least one basic banking account, financial literacy, and access to credit, insurance, and pension.',
    benefits:
      'Zero-balance savings account. RuPay debit card with ₹1 lakh accident insurance. ₹30,000 life insurance cover. Overdraft facility up to ₹10,000. Direct benefit transfer (DBT) linkage for government schemes.',
    eligibility:
      'Any Indian citizen aged 10 years and above. No minimum balance requirement. KYC-based account opening.',
    application_process:
      'Visit the nearest bank branch or Business Correspondent with Aadhaar and fill the account opening form. Accounts can also be opened at banking correspondents in villages.',
    required_documents:
      'Aadhaar card (or other KYC documents), passport-size photograph.',
    beneficiary_tags: ['All Citizens', 'Rural Household', 'Women', 'Farmer'],
    relevant_user_types: ['farmer', 'rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://pmjdy.gov.in',
    helpline: '1800-11-0001',
    launched_year: 2014,
    budget_outlay: null,
    tags: ['financial inclusion', 'bank account', 'RuPay card', 'zero balance', 'DBT'],
  },

  // ─────────────────────────────────────────────────────────
  // 31. PMJJBY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pmjjby',
    short_name: 'PMJJBY',
    official_name: 'Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)',
    scheme_type: 'INSURANCE',
    category: 'Social Security',
    subcategory: 'Life Insurance',
    ministry: 'Ministry of Finance / Department of Financial Services',
    department: 'Department of Financial Services',
    implementing_authority: 'Life Insurance Company of India (LIC) and other life insurance companies',
    description:
      'PMJJBY is a government-backed life insurance scheme that offers ₹2 lakh life insurance cover for a nominal annual premium of ₹436. It covers death due to any cause (natural or accidental). The scheme is available to bank account holders aged 18 to 50 years and is renewed annually. This scheme has brought affordable life insurance to crores of previously uninsured Indians.',
    objective:
      'To provide affordable life insurance coverage to citizens, especially the poor and low-income population, protecting families against the financial impact of the breadwinner\'s death.',
    benefits:
      '₹2 lakh death benefit for any cause of death. Annual premium of ₹436 auto-debited from savings account. Easy enrolment through bank. Group insurance scheme ensuring low cost.',
    eligibility:
      'Bank account holders aged 18 to 50 years. Must have Aadhaar linked to bank account. Auto-debit consent required.',
    application_process:
      'Enrol through bank branch, internet banking, or mobile banking. Give auto-debit consent for annual premium deduction. Also available through Business Correspondents.',
    required_documents:
      'Bank account details, Aadhaar number, mobile number.',
    beneficiary_tags: ['All Citizens', 'Farmer', 'Rural Household', 'Women'],
    relevant_user_types: ['farmer', 'rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://jansuraksha.gov.in',
    helpline: '1800-180-1111',
    launched_year: 2015,
    budget_outlay: null,
    tags: ['life insurance', 'social security', '₹2 lakh cover', 'affordable insurance', 'Jan Suraksha'],
  },

  // ─────────────────────────────────────────────────────────
  // 32. PMSBY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pmsby',
    short_name: 'PMSBY',
    official_name: 'Pradhan Mantri Suraksha Bima Yojana (PMSBY)',
    scheme_type: 'INSURANCE',
    category: 'Social Security',
    subcategory: 'Accident Insurance',
    ministry: 'Ministry of Finance / Department of Financial Services',
    department: 'Department of Financial Services',
    implementing_authority: 'Public sector general insurance companies and other general insurers',
    description:
      'PMSBY is a government-backed accident insurance scheme that provides accidental death and disability cover of ₹2 lakh for death or full disability, and ₹1 lakh for partial disability, for an annual premium of just ₹20. The scheme is available to savings bank account holders aged 18 to 70 years. Premium is auto-debited from the bank account, making it extremely easy to remain covered.',
    objective:
      'To provide affordable accidental insurance coverage to citizens, especially the uninsured poor, protecting against accidental death and disability.',
    benefits:
      '₹2 lakh for accidental death or permanent total disability. ₹1 lakh for permanent partial disability. Annual premium of just ₹20. Auto-debit from bank account for seamless renewal.',
    eligibility:
      'Savings bank account holders aged 18 to 70 years. One account per person. Aadhaar must be linked to bank account.',
    application_process:
      'Enrol at the bank through branch, internet banking, mobile banking, or business correspondents. Give consent for annual auto-debit of ₹20 premium.',
    required_documents:
      'Bank account details, Aadhaar number, mobile number.',
    beneficiary_tags: ['All Citizens', 'Farmer', 'Rural Household', 'Women'],
    relevant_user_types: ['farmer', 'rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://jansuraksha.gov.in',
    helpline: '1800-180-1111',
    launched_year: 2015,
    budget_outlay: null,
    tags: ['accident insurance', 'disability cover', '₹20 premium', 'Jan Suraksha', 'social security'],
  },

  // ─────────────────────────────────────────────────────────
  // 33. Atal Pension Yojana
  // ─────────────────────────────────────────────────────────
  {
    slug: 'atal-pension-yojana',
    short_name: 'APY',
    official_name: 'Atal Pension Yojana (APY)',
    scheme_type: 'SCHEME',
    category: 'Social Security',
    subcategory: 'Pension',
    ministry: 'Ministry of Finance / Pension Fund Regulatory and Development Authority (PFRDA)',
    department: 'Department of Financial Services',
    implementing_authority: 'Pension Fund Regulatory and Development Authority (PFRDA), Banks',
    description:
      'Atal Pension Yojana is a government-backed pension scheme primarily targeted at unorganised sector workers. Subscribers can choose a monthly pension of ₹1,000 to ₹5,000 upon reaching age 60, with contributions varying based on age of entry and chosen pension amount. The government co-contributes 50% of the total contribution or ₹1,000 per year (whichever is lower) for subscribers who joined before 2015–16 cut-off.',
    objective:
      'To provide a universal social security system for all Indians, especially the unorganised sector workers, by offering guaranteed pension after retirement.',
    benefits:
      'Guaranteed minimum pension of ₹1,000–₹5,000 per month after age 60. If subscriber dies, spouse gets pension; if spouse dies, corpus returned to nominee. Government co-contributed for early joiners.',
    eligibility:
      'Indian citizens aged 18 to 40 years with a savings bank account. Must not be income tax payers (from Oct 2022 onwards, income tax payers are excluded). Should not be covered under any statutory social security scheme.',
    application_process:
      'Enrol at any bank branch or through internet banking/mobile banking. Fill the APY registration form. Contribution auto-debited monthly from savings account.',
    required_documents:
      'Aadhaar card, savings bank account, mobile number.',
    beneficiary_tags: ['All Citizens', 'Farmer', 'Rural Household', 'Women', 'Youth'],
    relevant_user_types: ['farmer', 'rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.npscra.nsdl.co.in/scheme-details.php',
    helpline: '1800-110-069',
    launched_year: 2015,
    budget_outlay: null,
    tags: ['pension', 'retirement', 'unorganised sector', 'PFRDA', 'social security'],
  },

  // ─────────────────────────────────────────────────────────
  // 34. Rashtriya Gokul Mission
  // ─────────────────────────────────────────────────────────
  {
    slug: 'rashtriya-gokul-mission',
    short_name: 'RGM',
    official_name: 'Rashtriya Gokul Mission (RGM)',
    scheme_type: 'SCHEME',
    category: 'Dairy & Animal Husbandry',
    subcategory: 'Indigenous Breed Conservation',
    ministry: 'Ministry of Fisheries Animal Husbandry and Dairying',
    department: 'Department of Animal Husbandry and Dairying',
    implementing_authority: 'Department of Animal Husbandry and Dairying, State Governments',
    description:
      'Rashtriya Gokul Mission aims to conserve, develop, and propagate indigenous bovine breeds to enhance their genetic merit and improve productivity. The mission supports establishment of Gokul Grams (integrated bovine centres), strengthens bulls stations, and promotes modern breed improvement technologies like sex-sorted semen and In Vitro Fertilisation (IVF). It also provides financial assistance for establishing Pashu Sanjivani (Animal Health Management Programme) for all bovine animals.',
    objective:
      'To conserve and develop indigenous bovine breeds using modern scientific interventions and to enhance the production of high genetic merit bulls for quality germplasm supply across the country.',
    benefits:
      'Free animal health camps and Pashu Sanjivani for disease diagnosis. High-quality artificial insemination services at farmers\' doorstep. Establishment of Gokul Grams for breeding. Sex-sorted semen technology for more female calves.',
    eligibility:
      'Dairy farmers and livestock owners with indigenous bovine breeds. All bovine-owning farmers for Pashu Sanjivani programme.',
    application_process:
      'Benefits provided through state animal husbandry departments, veterinary centres, and paravets. Artificial insemination provided at village level through Pashu Sakhis and field veterinarians.',
    required_documents:
      'Aadhaar, animal ownership documentation.',
    beneficiary_tags: ['Dairy Farmer', 'Livestock Farmer', 'Farmer', 'Rural Household'],
    relevant_user_types: ['farmer', 'rural_stakeholder'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://dahd.nic.in',
    helpline: null,
    launched_year: 2014,
    budget_outlay: '₹2,400 crore (approx)',
    tags: ['indigenous breeds', 'Gokul', 'artificial insemination', 'bovine', 'dairy genetics'],
  },

  // ─────────────────────────────────────────────────────────
  // 35. NPDD
  // ─────────────────────────────────────────────────────────
  {
    slug: 'npdd',
    short_name: 'NPDD',
    official_name: 'National Programme for Dairy Development (NPDD)',
    scheme_type: 'PROGRAMME',
    category: 'Dairy & Animal Husbandry',
    subcategory: 'Dairy Infrastructure',
    ministry: 'Ministry of Fisheries Animal Husbandry and Dairying',
    department: 'Department of Animal Husbandry and Dairying',
    implementing_authority: 'NDDB, State Dairy Federations, State Governments',
    description:
      'NPDD provides financial assistance to dairy cooperative infrastructure to enhance milk procurement, processing, and marketing capabilities. The programme funds creation and modernisation of dairy infrastructure including chilling plants, processing plants, and equipment at dairy cooperative and private level. It helps states establish integrated dairy development projects that benefit milk producers through the cooperative supply chain.',
    objective:
      'To create and strengthen dairy infrastructure primarily for cooperative and farmer-owned institutions, increasing milk procurement, processing, and market access for dairy farmers.',
    benefits:
      'Capital investment grants for dairy cooperative infrastructure. Improved milk procurement and chilling network. Higher milk prices for dairy farmers through cooperative marketing. Dairy development in underserved states.',
    eligibility:
      'State Dairy Cooperatives, State Milk Federations, cooperative dairy plants, and in some components, private dairy entities.',
    application_process:
      'State governments submit proposals through NDDB to Ministry of Fisheries Animal Husbandry and Dairying. Projects are appraised and sanctioned. Implementation through NDDB and state federations.',
    required_documents:
      'Project DPR, state government guarantee, cooperative society registration, land documents.',
    beneficiary_tags: ['Dairy Farmer', 'Cooperative', 'Rural Household'],
    relevant_user_types: ['farmer', 'cooperative_member', 'cooperative_official'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://dahd.nic.in',
    helpline: null,
    launched_year: 2014,
    budget_outlay: '₹1,790 crore (approx)',
    tags: ['dairy infrastructure', 'milk chilling', 'cooperative dairy', 'NDDB', 'milk procurement'],
  },

  // ─────────────────────────────────────────────────────────
  // 36. AHIDF
  // ─────────────────────────────────────────────────────────
  {
    slug: 'ahidf',
    short_name: 'AHIDF',
    official_name: 'Animal Husbandry Infrastructure Development Fund (AHIDF)',
    scheme_type: 'FUND',
    category: 'Dairy & Animal Husbandry',
    subcategory: 'Animal Husbandry Infrastructure',
    ministry: 'Ministry of Fisheries Animal Husbandry and Dairying',
    department: 'Department of Animal Husbandry and Dairying',
    implementing_authority: 'NABARD, Scheduled Commercial Banks, Department of Animal Husbandry and Dairying',
    description:
      'AHIDF provides credit-linked investment support for setting up animal husbandry infrastructure like dairy processing plants, meat processing units, animal feed plants, and breed improvement facilities. The fund offers 3% interest subvention on loans from banks for eligible projects. Incentives are provided to MSMEs, private companies, FPOs, and individual entrepreneurs who invest in animal husbandry value chains.',
    objective:
      'To incentivise private investment in dairy processing, value addition, meat processing, animal feed, and breed improvement infrastructure to strengthen the entire animal husbandry value chain.',
    benefits:
      '3% interest subvention on loans for 5 years. 90% bank financing with 10% promoter equity. Eligible entities: individual, FPOs, MSMEs, companies, section 8 companies. Credit guarantee support.',
    eligibility:
      'MSMEs, private companies, FPOs, SHGs, and individual entrepreneurs in dairy processing, meat processing, animal feed, and breed improvement sectors.',
    application_process:
      'Apply online through NABARD or participating banks with a project report. Applications are evaluated by a National Advisory Committee. NABARD monitors implementation.',
    required_documents:
      'Project DPR, entity registration, promoter identity documents, financial statements, land documents, bank account details.',
    beneficiary_tags: ['Dairy Farmer', 'Livestock Farmer', 'FPO', 'Entrepreneur', 'Cooperative'],
    relevant_user_types: ['farmer', 'cooperative_official', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://dahd.nic.in',
    helpline: null,
    launched_year: 2020,
    budget_outlay: '₹15,000 crore',
    tags: ['dairy processing', 'meat processing', 'animal feed', 'interest subvention', 'AHIDF'],
  },

  // ─────────────────────────────────────────────────────────
  // 37. National Livestock Mission
  // ─────────────────────────────────────────────────────────
  {
    slug: 'national-livestock-mission',
    short_name: 'NLM',
    official_name: 'National Livestock Mission (NLM)',
    scheme_type: 'SCHEME',
    category: 'Dairy & Animal Husbandry',
    subcategory: 'Livestock Development',
    ministry: 'Ministry of Fisheries Animal Husbandry and Dairying',
    department: 'Department of Animal Husbandry and Dairying',
    implementing_authority: 'Department of Animal Husbandry and Dairying, State Governments, NABARD',
    description:
      'National Livestock Mission aims to increase production and productivity of livestock (goats, sheep, pigs, poultry, and other small animals) while ensuring adequate availability of quality feed and fodder. The mission provides entrepreneurship development support and subsidies for setting up livestock enterprises, fodder development, and breed improvement for non-bovine livestock. It targets landless, marginal farmers, and tribal populations.',
    objective:
      'To ensure quantitative and qualitative improvement in livestock production systems and sustainable growth of livestock sector, with focus on small ruminants, pigs, poultry, and fodder development.',
    benefits:
      'Credit-linked subsidy of 50% (60% for SC/ST/NE/hilly states) for livestock enterprise establishment. Support for fodder and feed development. Breed improvement through progeny testing and selection. Employment generation through livestock entrepreneurship.',
    eligibility:
      'Farmers, landless labourers, SHGs, FPOs, individual entrepreneurs, cooperatives, and state government agencies. Priority for small ruminant and poultry farmers.',
    application_process:
      'Apply through state animal husbandry departments or online at NLM portal (nlm.udyamimitra.in). State governments identify beneficiaries and implement through district offices.',
    required_documents:
      'Aadhaar, land records or landlessness certificate, bank account details, project proposal for enterprise, caste certificate if applicable.',
    beneficiary_tags: ['Livestock Farmer', 'Farmer', 'Women', 'Rural Household', 'Entrepreneur'],
    relevant_user_types: ['farmer', 'rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://nlm.udyamimitra.in',
    helpline: null,
    launched_year: 2014,
    budget_outlay: '₹2,300 crore (approx)',
    tags: ['livestock', 'goat', 'poultry', 'fodder', 'animal husbandry enterprise'],
  },

  // ─────────────────────────────────────────────────────────
  // 38. PMMSY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pmmsy',
    short_name: 'PMMSY',
    official_name: 'Pradhan Mantri Matsya Sampada Yojana (PMMSY)',
    scheme_type: 'SCHEME',
    category: 'Fisheries',
    subcategory: 'Fisheries Development',
    ministry: 'Ministry of Fisheries Animal Husbandry and Dairying',
    department: 'Department of Fisheries',
    implementing_authority: 'Department of Fisheries, State Governments, NFDB',
    description:
      'PMMSY is the flagship scheme for fisheries sector development with an investment of ₹20,050 crore over 5 years. It aims to double fish production to 220 lakh MT by 2024–25, double fishers\' incomes, modernise fishing fleets, and establish post-harvest and cold chain infrastructure. The scheme covers marine and inland fisheries, aquaculture, and welfare of fishers.',
    objective:
      'To bring about Blue Revolution in fisheries sector through sustainable and responsible development for economic prosperity of fishers and fish farmers, production growth, and increase in exports.',
    benefits:
      'Subsidy of 40–60% for eligible activities for fishers, fish farmers, and coastal/inland fishers. Financial support for construction/renovation of fishing boats, nets, cages, hatcheries, RAS, etc. Accident insurance for fishers. Ice plants, cold storage, and fish markets support.',
    eligibility:
      'Fishers, fish farmers, fish workers, SHGs, FPOs, cooperatives, fisheries federations, and state/UT governments.',
    application_process:
      'Applications submitted to Department of Fisheries at state/UT level. Online applications through state government portals. NFDB processes central component applications.',
    required_documents:
      'Aadhaar, fishing licence (where applicable), land/water body lease documents, bank account details, project proposal.',
    beneficiary_tags: ['Fisher', 'Cooperative', 'FPO', 'Women', 'Rural Household'],
    relevant_user_types: ['rural_stakeholder', 'cooperative_member', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://pmmsy.dof.gov.in',
    helpline: null,
    launched_year: 2020,
    budget_outlay: '₹20,050 crore (2020–25)',
    tags: ['fisheries', 'aquaculture', 'Blue Revolution', 'fish production', 'NFDB'],
  },

  // ─────────────────────────────────────────────────────────
  // 39. PM-MKSSY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pm-mkssy',
    short_name: 'PM-MKSSY',
    official_name: 'PM Matsya Kisan Samridhi Sah-Yojana (PM-MKSSY)',
    scheme_type: 'SCHEME',
    category: 'Fisheries',
    subcategory: 'Fish Farmer Welfare',
    ministry: 'Ministry of Fisheries Animal Husbandry and Dairying',
    department: 'Department of Fisheries',
    implementing_authority: 'Department of Fisheries, State Governments',
    description:
      'PM-MKSSY is a sub-scheme under PMMSY focusing on formalisation and welfare of the fisheries sector through registration and ID cards for fishers, fish farmers, and fish workers. It provides performance-based incentives for fishers and fish farmers for sustainable practices. The scheme also supports institutional credit, aquaculture insurance, and microenterprise development in the fisheries sector.',
    objective:
      'To formalise the fisheries micro and small enterprise sector, provide social, physical, and economic security to fishers and fish farmers through unique identification and targeted scheme benefits.',
    benefits:
      'Performance-based incentive up to ₹3,000 per fish farmer per crop season for sustainable practices. Aquaculture insurance. Institutional credit facilitation. Formalisation through fish farmer registration and ID cards.',
    eligibility:
      'Fishers, fish farmers, fish workers, and fish vendors who register on the fisheries database portal.',
    application_process:
      'Registration through state fisheries department portals or through the PM-MKSSY registration platform. Incentives disbursed after verification of sustainable practices.',
    required_documents:
      'Aadhaar, fishing licence (where applicable), bank account details, mobile number, relevant activity documents.',
    beneficiary_tags: ['Fisher', 'Farmer', 'Women', 'Rural Household'],
    relevant_user_types: ['rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://pmmsy.dof.gov.in',
    helpline: null,
    launched_year: 2023,
    budget_outlay: '₹6,000 crore (approx, over sub-scheme period)',
    tags: ['fish farmer welfare', 'fisheries formalisation', 'aquaculture', 'fisher ID', 'PMMSY sub-scheme'],
  },

  // ─────────────────────────────────────────────────────────
  // 40. FIDF
  // ─────────────────────────────────────────────────────────
  {
    slug: 'fidf',
    short_name: 'FIDF',
    official_name: 'Fisheries and Aquaculture Infrastructure Development Fund (FIDF)',
    scheme_type: 'FUND',
    category: 'Fisheries',
    subcategory: 'Fisheries Infrastructure',
    ministry: 'Ministry of Fisheries Animal Husbandry and Dairying / NABARD',
    department: 'Department of Fisheries',
    implementing_authority: 'NABARD, Scheduled Commercial Banks, State Governments',
    description:
      'FIDF provides concessional credit to state governments, state entities, and private entrepreneurs for creation of fisheries infrastructure such as fishing harbours, fish landing centres, refrigerated sea-water systems, and aquaculture infrastructure. The fund offers interest subvention to reduce the cost of credit for fisheries infrastructure projects. It aims to address the critical infrastructure gap in the marine and inland fisheries sectors.',
    objective:
      'To address the fisheries infrastructure deficit by providing affordable credit for creation and modernisation of fishing harbours, fish landing centres, cold chain, and aquaculture facilities.',
    benefits:
      'Interest subvention of 3% on loans for fisheries infrastructure. Long repayment tenors for infrastructure projects. Credit for fishing harbours, fish landing centres, cold storage, aquaculture infrastructure.',
    eligibility:
      'State governments, Union Territories, state-owned corporations, and private entrepreneurs in the fisheries sector.',
    application_process:
      'Proposals submitted to NABARD or participating banks. State governments facilitate applications from state entities. Appraised and sanctioned by NABARD.',
    required_documents:
      'DPR for infrastructure project, entity registration, land documents, financial statements, NOC from relevant authorities.',
    beneficiary_tags: ['Fisher', 'Cooperative', 'Entrepreneur', 'Rural Household'],
    relevant_user_types: ['rural_stakeholder', 'cooperative_official', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://www.nabard.org',
    helpline: null,
    launched_year: 2018,
    budget_outlay: '₹7,522 crore',
    tags: ['fisheries infrastructure', 'fishing harbour', 'cold chain', 'NABARD', 'interest subvention'],
  },

  // ─────────────────────────────────────────────────────────
  // 41. MGNREGA
  // ─────────────────────────────────────────────────────────
  {
    slug: 'mgnrega',
    short_name: 'MGNREGA',
    official_name: 'Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA)',
    scheme_type: 'SCHEME',
    category: 'Rural Employment',
    subcategory: 'Wage Employment Guarantee',
    ministry: 'Ministry of Rural Development',
    department: 'Department of Rural Development',
    implementing_authority: 'State Government Rural Development Departments, Gram Panchayats',
    description:
      'MGNREGA guarantees 100 days of wage employment per year to every rural household whose adult members volunteer to do unskilled manual work. Work is provided within 15 days of demand or unemployment allowance is paid. The scheme creates durable assets like roads, ponds, farm bunds, and irrigation works in rural areas. Wages are paid directly to bank/post office accounts of workers.',
    objective:
      'To enhance the livelihood security of rural households by providing at least 100 days of guaranteed wage employment in a financial year to every rural household whose adult members volunteer to do unskilled manual work.',
    benefits:
      '100 days of guaranteed wage employment per rural household per year. Statutory minimum wages paid (State-notified MGNREGA wages). Unemployment allowance if work not provided within 15 days. Creation of durable rural assets. Women get preference (33% reservation).',
    eligibility:
      'Any adult member of a rural household willing to do unskilled manual work. Must reside in the village where the work is demanded.',
    application_process:
      'Register at Gram Panchayat with household details and obtain a Job Card (free of cost). Demand work in writing to Gram Panchayat. Work allocated within 15 days of demand.',
    required_documents:
      'Aadhaar, bank/post office account details, residence proof, passport-size photographs.',
    beneficiary_tags: ['Rural Household', 'Women', 'Farmer', 'Youth'],
    relevant_user_types: ['rural_stakeholder', 'farmer'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://nrega.nic.in',
    helpline: '1800-111-555',
    launched_year: 2006,
    budget_outlay: '₹73,000 crore per year (approx)',
    tags: ['wage employment', 'job guarantee', 'rural work', 'unskilled labour', 'rural assets'],
  },

  // ─────────────────────────────────────────────────────────
  // 42. PMAY-G
  // ─────────────────────────────────────────────────────────
  {
    slug: 'pmay-g',
    short_name: 'PMAY-G',
    official_name: 'Pradhan Mantri Awaas Yojana – Gramin (PMAY-G)',
    scheme_type: 'SCHEME',
    category: 'Rural Housing',
    subcategory: 'Housing for Rural Poor',
    ministry: 'Ministry of Rural Development',
    department: 'Department of Rural Development',
    implementing_authority: 'State Rural Development Departments, Gram Panchayats',
    description:
      'PMAY-G provides financial assistance to eligible rural households living in kutcha (temporary) houses or without houses to build a pucca (permanent) house with basic amenities. Financial assistance of ₹1.20 lakh (plain areas) or ₹1.30 lakh (hilly/difficult areas) is provided directly to beneficiary accounts in tranches. The scheme is targeted at the homeless and those living in kutcha houses based on SECC 2011 data.',
    objective:
      'To provide a pucca house with basic facilities to all rural households that are houseless or living in dilapidated houses by 2024.',
    benefits:
      '₹1.20 lakh financial assistance for plain areas; ₹1.30 lakh for hilly/difficult areas. ₹12,000 for construction of toilet under SBM (convergence). 90 days of unskilled wage labour under MGNREGA for house construction. Direct benefit transfer to beneficiary bank accounts.',
    eligibility:
      'Houseless rural households or those with kutcha/dilapidated houses. Identified from SECC 2011 data and awaiting house construction. Priority: SC/ST, freed bonded labourers, minorities, persons with disability.',
    application_process:
      'Beneficiaries identified from SECC 2011 list by Gram Panchayat. No separate application needed; Gram Panchayats confirm eligibility and work orders issued. AwaasSoft MIS tracks construction.',
    required_documents:
      'Aadhaar, bank account details, land documents (where applicable), mobile number.',
    beneficiary_tags: ['Rural Household', 'Women', 'Farmer'],
    relevant_user_types: ['rural_stakeholder', 'farmer'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://pmayg.nic.in',
    helpline: '1800-11-6446',
    launched_year: 2016,
    budget_outlay: '₹2,17,257 crore (2016–24)',
    tags: ['rural housing', 'pucca house', 'SECC', 'BPL housing', 'affordable housing'],
  },

  // ─────────────────────────────────────────────────────────
  // 43. DAY-NRLM
  // ─────────────────────────────────────────────────────────
  {
    slug: 'day-nrlm',
    short_name: 'DAY-NRLM',
    official_name: 'Deen Dayal Antyodaya Yojana – National Rural Livelihoods Mission (DAY-NRLM)',
    scheme_type: 'SCHEME',
    category: 'Rural Livelihoods',
    subcategory: 'SHG & Livelihood Promotion',
    ministry: 'Ministry of Rural Development',
    department: 'Department of Rural Development',
    implementing_authority: 'State Rural Livelihoods Missions, Gram Panchayats, SHG Federations',
    description:
      'DAY-NRLM promotes poverty reduction by organising the rural poor into Self-Help Groups (SHGs) and federations, providing them access to credit and livelihood opportunities. Women from below-poverty-line households are mobilised into SHGs, linked with bank credit, and supported to take up diversified livelihood activities. The mission also provides skill training and placement support under its AAJEEVIKA component.',
    objective:
      'To reduce poverty by enabling rural households to access improved and diversified livelihoods, by mobilising rural poor into SHGs, providing credit linkage, and building skills and capacities.',
    benefits:
      'Interest subvention for SHG loans (7% interest, 3% for timely repayment). Revolving fund of ₹10,000–₹15,000 per SHG. Community Investment Fund for livelihood activities. Skill training and placement support. Bank linkage for SHG members.',
    eligibility:
      'Rural poor households, particularly women from BPL and economically weaker sections. SHGs with 10–15 women members from poor households.',
    application_process:
      'Women organise into SHGs with support of Community Resource Persons and State Mission staff. SHGs register and open bank accounts. Credit linkage through banks. Applications through State Rural Livelihoods Mission offices.',
    required_documents:
      'Aadhaar, BPL/SECC identification, bank account details, SHG registration documents.',
    beneficiary_tags: ['SHG', 'Women', 'Rural Household', 'Farmer'],
    relevant_user_types: ['rural_stakeholder', 'farmer'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://aajeevika.gov.in',
    helpline: '1800-180-2087',
    launched_year: 2011,
    budget_outlay: '₹14,236 crore per year (approx)',
    tags: ['SHG', 'self-help group', 'women empowerment', 'rural livelihoods', 'AAJEEVIKA'],
  },

  // ─────────────────────────────────────────────────────────
  // 44. DDU-GKY
  // ─────────────────────────────────────────────────────────
  {
    slug: 'ddu-gky',
    short_name: 'DDU-GKY',
    official_name: 'Deen Dayal Upadhyaya Grameen Kaushalya Yojana (DDU-GKY)',
    scheme_type: 'SCHEME',
    category: 'Rural Skills & Employment',
    subcategory: 'Rural Youth Skill Development',
    ministry: 'Ministry of Rural Development',
    department: 'Department of Rural Development',
    implementing_authority: 'State Rural Livelihoods Missions, Project Implementing Agencies (PIAs)',
    description:
      'DDU-GKY is a placement-linked skill development programme that targets rural youth from poor families and trains them for market-demanded skills in sectors like hospitality, retail, construction, healthcare, and more. The scheme guarantees post-training placement with a minimum salary of ₹6,000 per month. Training is fully funded by the government, and trainees receive post-placement support for career progression.',
    objective:
      'To reduce poverty by diversifying income of rural families and enabling employment-oriented skill development and placement of rural youth in market-determined jobs with regular monthly wages.',
    benefits:
      'Free skill training for rural youth. Guaranteed placement in regular salaried jobs. Post-placement support and career progression. Training in 50+ job roles across 25+ sectors. Training includes food, accommodation, and transport.',
    eligibility:
      'Rural youth aged 15–35 years (up to 45 for SC/ST, women, PWD, ex-servicemen) from poor households (SECC identified). Must be willing to work for salaried employment post-training.',
    application_process:
      'Youth apply through State RLMS offices, through Project Implementing Agencies, or through common mobilisation campaigns in villages.',
    required_documents:
      'Aadhaar, age proof (school certificate/birth certificate), SECC/BPL identification, educational qualification certificate, bank account details.',
    beneficiary_tags: ['Youth', 'Women', 'Rural Household'],
    relevant_user_types: ['rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://ddugky.gov.in',
    helpline: '1800-180-6127',
    launched_year: 2014,
    budget_outlay: '₹1,500 crore per year (approx)',
    tags: ['skill development', 'rural youth', 'placement linked', 'vocational training', 'wage employment'],
  },

  // ─────────────────────────────────────────────────────────
  // 45. NSAP
  // ─────────────────────────────────────────────────────────
  {
    slug: 'nsap',
    short_name: 'NSAP',
    official_name: 'National Social Assistance Programme (NSAP)',
    scheme_type: 'SCHEME',
    category: 'Social Security',
    subcategory: 'Social Assistance for Poor',
    ministry: 'Ministry of Rural Development',
    department: 'Department of Rural Development',
    implementing_authority: 'State Governments, Gram Panchayats, State Nodal Departments',
    description:
      'NSAP provides financial assistance to the elderly, widows, disabled persons, and bereaved families below the poverty line through five sub-schemes: Indira Gandhi National Old Age Pension Scheme (IGNOAPS), Indira Gandhi National Widow Pension Scheme (IGNWPS), Indira Gandhi National Disability Pension Scheme (IGNDPS), National Family Benefit Scheme (NFBS), and Annapurna. Monthly pensions range from ₹200 to ₹500 under central component, often enhanced by states.',
    objective:
      'To provide social protection to the poorest households including the aged, widowed, disabled, and bereaved by providing pension and financial assistance as a social safety net.',
    benefits:
      'Monthly pension of ₹200 (60–79 years) and ₹500 (80+ years) under IGNOAPS. ₹300/month for widows under IGNWPS. ₹300/month for disabled under IGNDPS. ₹20,000 lump sum on breadwinner\'s death under NFBS. 10 kg rice/wheat per month under Annapurna.',
    eligibility:
      'BPL households: Elderly aged 60+ (IGNOAPS); widows aged 40–79 (IGNWPS); severely/multiple disabled aged 18–79 (IGNDPS); BPL households where breadwinner dies aged 18–60 (NFBS); destitute aged 65+ not covered under any other pension (Annapurna).',
    application_process:
      'Applications submitted to Gram Panchayat/Block Development Officer with required documents. State governments process and include in pension roll. Pension disbursed directly to bank/post office accounts.',
    required_documents:
      'Aadhaar, BPL card/SECC identification, age proof, disability certificate (for IGNDPS), death certificate of breadwinner (for NFBS), bank account details.',
    beneficiary_tags: ['Rural Household', 'Women', 'All Citizens'],
    relevant_user_types: ['rural_stakeholder', 'other'],
    geographic_scope: 'NATIONAL',
    applicable_states: [],
    status: 'ACTIVE',
    official_url: 'https://nsap.nic.in',
    helpline: null,
    launched_year: 1995,
    budget_outlay: '₹9,636 crore per year (approx)',
    tags: ['pension', 'old age', 'widow', 'disability', 'social assistance'],
  },
] as const satisfies SchemeEntry[]

// ============================================================
// Helper Functions
// ============================================================

/**
 * Returns all schemes that belong to the given category.
 */
export function getSchemesByCategory(category: string): SchemeEntry[] {
  return SCHEMES_CATALOGUE.filter(
    (s) => s.category.toLowerCase() === category.toLowerCase()
  ) as SchemeEntry[]
}

/**
 * Returns all schemes that include the given beneficiary tag.
 */
export function getSchemesByBeneficiary(tag: string): SchemeEntry[] {
  return SCHEMES_CATALOGUE.filter((s) =>
    (s.beneficiary_tags as readonly string[]).includes(tag)
  ) as SchemeEntry[]
}

/**
 * Returns the scheme matching the given slug, or undefined if not found.
 */
export function getSchemeBySlug(slug: string): SchemeEntry | undefined {
  return SCHEMES_CATALOGUE.find((s) => s.slug === slug) as SchemeEntry | undefined
}

/**
 * Sorted list of unique scheme categories present in the catalogue.
 */
export const SCHEME_CATEGORIES: string[] = Array.from(
  new Set(SCHEMES_CATALOGUE.map((s) => s.category))
).sort()

/**
 * All possible beneficiary tag values.
 */
export const BENEFICIARY_TAGS: string[] = [
  'Farmer',
  'PACS',
  'Cooperative',
  'FPO',
  'SHG',
  'Women',
  'Youth',
  'Entrepreneur',
  'Fisher',
  'Dairy Farmer',
  'Rural Household',
  'Livestock Farmer',
  'All Citizens',
] as const
