import streamlit as st
from openai import OpenAI
import json
import pandas as pd
from requests import request

#clear cache
st.cache_data.clear() 
st.cache_resource.clear()

#function for getting drug data from FDA usig its open API
def get_drug_info(drug):
    
    try:
        url_fda_drug=f"https://api.fda.gov/drug/drugsfda.json?search=openfda.brand_name:{drug}"
        r=request("GET", url_fda_drug)
    except request.exceptions.RequestException as e:
        st.write("warning")
    try:
        drug_info=r.json()
        #create 2 columns, 1 for active ingredients using a loop and one for dosage information
        column1, column2=st.columns(2)
        #check if drug is not in database
        if "error" not in drug_info:
            with column1:
                for item in drug_info["results"][0]["products"][0]["active_ingredients"]:
                    st.write("Name: ", item["name"])
                    st.write("Strength: ", item["strength"])
            
            with column2:
                st.subheader("Dosage", drug_info["results"][0]["products"][0]["dosage_form"])
                st.write("Dosage Form: ", drug_info["results"][0]["products"][0]["dosage_form"])
                st.write("Route: ", drug_info["results"][0]["products"][0]["route"])
        else:
            st.write("Can't find the drug in database")
    except json.JSONDecodeError:
        st.error("Failed to decode the response into JSON. Please check the name of the drug.")


# Set your OpenAI API key here
client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

def get_disease_info(disease_name):
    """
    Function to query OpenAI and return structured information about a disease.
    """
    medication_format = '''"name":""
    "side_effects":[
    0:""
    1:""
    ...
    ]
    "dosage":""'''
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"Please provide information on the following aspects for {disease_name}: 1. Key Statistics, 2. Recovery Options, 3. Recommended Medications. Format the response in JSON with keys for 'name', 'statistics', 'total_cases' (this always has to be a number), 'recovery_rate' (this always has to be a percentage), 'mortality_rate' (this always has to be a percentage) 'recovery_options', (explain each recovery option in detail), and 'medication', (give some side effect examples and dosages) always use this json format for medication : {medication_format} ."}
        ]
    )
    return response.choices[0].message.content

def display_disease_info(disease_info):
    """
    Function to display the disease information in a structured way using Streamlit.
    """
    try:
        info = json.loads(disease_info)

        recovery_rate = float(info['statistics']["recovery_rate"].strip('%'))
        mortality_rate = float(info['statistics']["mortality_rate"].strip('%'))

        chart_data = pd.DataFrame(
            {
                "Recovery Rate": [recovery_rate],
                "Mortality Rate": [mortality_rate],
            },
            index = ["Rate"]  # This is a single index. You might adjust it based on your data structure.
        )

        st.write(f"## Statistics for {info['name']}")
        #st.write(info['statistics'])
        st.bar_chart(chart_data)
        st.write("## Recovery Options")
        recovery_options = info['recovery_options']
        for option, description in recovery_options.items():
            st.subheader(option)
            st.write(description)
        st.write("## Medication")
        medication = info['medication']
        medication_count = 1
        for option, description in medication.items():

            st.subheader(f"{medication_count}. {option}")
            st.write(description)
            medication_count += 1
    except json.JSONDecodeError:
        st.error("Failed to decode the response into JSON. Please check the format of the OpenAI response.")


st.title("Drug Information Dashboard")
#input for the drug of interest
drug=st.text_input("Enter the name of the drug")
if drug:
    get_drug_info(drug)

st.title("Disease Information Dashboard")
disease_name = st.text_input("Enter the name of the disease:")
if disease_name:
    disease_info = get_disease_info(disease_name)
    display_disease_info(disease_info)