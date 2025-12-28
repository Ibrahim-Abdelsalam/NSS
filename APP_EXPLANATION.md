# App.py Deep Dive - Verified Code Reference

**File**: `app.py`
**Coordinates**: Based on filesystem audit.

---

## Chunk 2: Data Input Logic (Lines 330-400)

### The File Uploader
```python
# Line 369
nurse_file = st.file_uploader(
    "Nurse List (CSV/TXT)", 
    type=["csv", "txt"],
    help="One nurse name per line"
)
```
**Detailed Logic**:
*   **Line 369**: Standard Streamlit widget. Handles parsing of uploaded byte streams.

---

## Chunk 3: Parameter Configuration (Lines 500-800)

### Work Rules Configuration
Coordinates for the constraint sliders.

```python
# Line 630
n1 = st.slider("Max Total Shifts ($n_1$)", 1, 30, 15, 1)

# Line 632
n3 = st.slider("Min Regular Shifts ($n_3$)", 0, 20, 5, 1)
```
**Detailed Logic**:
*   **Line 630**: `n1` input. Passed to Constraint 6.
*   **Line 632**: `n3` input. Passed to Constraint 8. Note the LaTeX syntax `$n_3$` in the label.

---

## Chunk 4: Execution Logic (Lines 880-1000)

### The Optimization Trigger
```python
# Line 889
if st.button("⚡ Optimize Schedule", type="primary", use_container_width=True, disabled=True):
    # ... logic ...
```
**Detailed Logic**:
*   **Line 889**: The primary action button.
    *   **Note**: It seems to have a `disabled=True` state conditionally (likely waits for data load).
*   **Line 1010**: `model_params = {...}` Dictionary creation happens *before* the button logic (Chunk 3).

---

## Chunk 5: Visualization (Lines 1360-1900)

### The Heatmap
```python
# Line 1784
fig_heatmap = px.imshow(
    numerical_schedule,
    x=day_labels,
    y=nurse_labels,
    color_continuous_scale=[[0, 'white'], [1, '#2563eb']]
)
```
**Detailed Logic**:
*   **Line 1784**: Plotly Express call.
*   **Line 1807**: There might be a duplicate call for the "Fatigue" heatmap or a conditional branch.

---

## Chunk 7: Export Logic (Lines 2100+)

```python
# Line 2153
st.download_button(
    "Download Roster (CSV)",
    data=csv,
    file_name="roster.csv"
)
```
**Detailed Logic**:
*   **Line 2153**: The final action in the workflow. Allows extraction of `roster_df`.
