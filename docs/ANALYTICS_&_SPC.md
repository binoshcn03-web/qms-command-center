# ANALYTICS_&_SPC.md: LSS & Statistical Modeling

## Advanced DAX: Lean Six Sigma & Statistical Process Control
This semantic model goes beyond descriptive analytics, embedding predictive algorithms, Lean Six Sigma methodologies, and automated FMEA prioritization directly into DAX.

### 1. Statistical Process Control (SPC) & Nelson Rules
To differentiate between common cause variation and special cause variation, the model establishes a native Control Chart framework.  

* **Standard Deviation & Control Limits:** Calculates dynamic boundaries for operational stability using `STDEV.P` across QA scores to generate the `UCL Quality` ($+3\sigma$) and `LCL Quality` ($-3\sigma$).  
* **Automated Nelson Rule 1 Detection:** Iterates through evaluation fact records to automatically flag instances where `ClientQualityScore` breaches the upper or lower control limits, rendering an `SPC In Control %` metric.  

### 2. Automated FMEA (Failure Mode and Effects Analysis)
The model automates risk assessment by assigning dynamic Risk Priority Numbers (RPN) to specific process failures.  

* **Occurrence** is calculated dynamically by rounding the Attribute Fail Rate into a 1-10 index.  
* **Severity** and **Detection** indices are structurally mapped in `Dim_QA_Parameter` based on the compliance or business criticality of the standard.  
* The resultant RPN measure multiplies these three variables and generates a dense-ranked FMEA Rank to dictate operational priorities.  

### 3. Process Capability & Six Sigma Metrics
The architecture isolates applicable lines and defects to compute standard manufacturing quality metrics applied to service operations.  

* **Yield & DPMO:** Calculates First Pass Yield and Defects Per Million Opportunities directly from the unpivoted evaluation fact table.  
* **Z-Score Approximation:** Natively calculates the Z-Score (process capability) without relying on external Python/R scripts, utilizing the approximation formula:  

$$Z \approx 4.56 \times p^{0.25} - 0.86 \times (1-p)^{0.25} - 1.85$$

*(where $p$ represents the Yield)*

### 4. Predictive Linear Regression (LINESTX)
The model anticipates future quality trajectories by deploying DAX's linear regression functions.  

* Extracts the continuous time series index (`DateIndex`) alongside the `Quality Mean`.  
* Deploys `LINESTX` to dynamically calculate the `Quality Slope` and `Quality Intercept`.  
* Projects the anticipated `Forecast Quality` by mapping the slope against future index dates.  

### 5. Pearson Correlation Iterators
The semantic model actively validates the hypothesis that internal QA scores drive customer satisfaction.  

* Implements a custom DAX iterator to manually compute the Pearson correlation coefficient ($r$) between the `ClientQualityScore` and the `CsatScore` gathered from CRM data.  

**Formula logic applied natively in DAX:**

$$r = \frac{\sum (Q - \bar{Q})(C - \bar{C})}{\sqrt{\sum (Q - \bar{Q})^2} \sqrt{\sum (C - \bar{C})^2}}$$