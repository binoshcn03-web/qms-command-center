# PROCESS.md: The Technical Deep-Dive

## Data Architecture & ETL Strategy

### ETL & Power Query Transformations
To ensure analytical flexibility and maximize DAX calculation speed, raw evaluation data undergoes rigorous structural transformation:

* **Dimensional Unpivoting:** The raw QA evaluation dataset arrives in a wide format, tracking 20 distinct quality parameters (`QP01_SecurityVerification` through `QP20_ClosingRecap`) as separate columns. Using Power Query, these columns are unpivoted to dynamically generate the `Fact_QA_Evaluation_Line` table.  
* **Defect Engineering:** During the ETL process, Boolean flags (`IsDefect`, `IsApplicable`) are engineered directly into the data model. This transition from a wide format to a long format is critical for performing granular Six Sigma calculations, such as Defects Per Million Opportunities (DPMO) and Yield.  

### Data Modeling & Relational Logic
The model is built on an enterprise-grade Star Schema with specific enhancements for dynamic security and dimensional swapping:

* **Parent-Child Hierarchies (Row-Level Security):** The `Dim_Employee` table utilizes native DAX pathing functions (`PATH`, `PATHLENGTH`, `PATHITEM`) to construct a flattened organizational reporting structure based on the `ManagerEmployeeID`. This architecture enables dynamic Row-Level Security (RLS), allowing leadership to seamlessly drill down from the site level to the individual agent view.  
* **Disconnected Tables for Field Parameters:** To enhance UX and prevent slicer fatigue, disconnected tables (`Parameter.tmdl`, `TCD Grain.tmdl`, `Coaching Performance Parameter.tmdl`) are deployed as Field Parameters. This allows users to dynamically swap the granularity of visual axes (e.g., toggling from `Level1Product` to `Level4ReasonDetail`) without navigating to separate report pages.  

### Business Logic & Automated Interventions
The semantic model actively encodes complex business rules to flag risks and calculate return on investment (ROI):

* **Training Needs Identification (TNI) Flag:** An automated diagnostic measure that calculates Defect Velocity by comparing defect counts over a rolling 30-day period against the prior 30 days. If velocity is positive and the Attribute Fail Rate exceeds an 8% threshold, the system flags the parameter for immediate "Intervention".  
* **Coaching ROI Proxy:** Merges quality coaching actions with financial outcomes. By isolating the Coaching Lift (Quality Score 30 days post-coaching minus 30 days pre-coaching) and multiplying it by the Cost of Poor Quality (COPQ), the model quantifies the financial ROI of targeted supervisor coaching.  
* **Dynamic New Hire Glide Paths:** Adapts the expected Glide Target dynamically based on the agent's `TenureBucket` (e.g., 0-30 days targets 70%, >180 days targets 88%). This ensures a fair Glide Gap assessment for agents actively progressing through their learning curve.