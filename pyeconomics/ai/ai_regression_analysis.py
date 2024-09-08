# pyeconomics/ai/ai_regression_analysis.py

import os
import openai
from statsmodels.regression.linear_model import RegressionResults
from statsmodels.stats.diagnostic import het_breuschpagan, linear_reset
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.stats.stattools import omni_normtest
from typing import Union
from IPython.display import display, Markdown

from pyeconomics.api.openai_api import load_prompt, initialize_openai_client
from ..data.model_parameters import ChatGPTParameters


def ai_regression_analysis(
    model: RegressionResults,
    ai_params: ChatGPTParameters = ChatGPTParameters()
) -> Union[None, str]:
    """
    Generate an AI-based analysis of the OLS regression results.

    Args:
        model (RegressionResults): A statsmodels OLS Regression Results object.
        ai_params (ChatGPTParameters): Instance containing the AI parameters.

    Returns:
        Union[None, str]: AI-generated analysis paragraph or None if Markdown
            output is enabled.
    """
    # Ensure the OpenAI client is initialized only when this function is called
    initialize_openai_client()

    # Extract the needed estimates from the ai_model
    slope_name = model.params.index[1]
    estimates = {
        'R_squared': model.rsquared,
        'Adj_R_squared': model.rsquared_adj,
        'F_statistic': model.fvalue,
        'Prob_F_statistic': model.f_pvalue,
        't_statistic': model.tvalues[slope_name],
        'P_value': model.pvalues[slope_name],
        'Omnibus': omni_normtest(model.resid)[0],
        'Prob(Omnibus)': omni_normtest(model.resid)[1],
        'Jarque-Bera': jarque_bera(model.resid)[0],
        'Prob(JB)': jarque_bera(model.resid)[1],
        'Skewness': model.resid.skew(),
        'Kurtosis': model.resid.kurtosis() + 3,
        'Breusch_Pagan': het_breuschpagan(model.resid, model.model.exog)[0],
        'Prob(BP)': het_breuschpagan(model.resid, model.model.exog)[1],
        'Durbin_Watson': durbin_watson(model.resid),
        'Condition_Number': model.condition_number,
        'Intercept': model.params['const'],
        'Slope': model.params[slope_name],
        'Slope_Name': slope_name,
        'Ramsey_Reset': linear_reset(model, power=2, use_f=True).fvalue,
        'Prob(RR)': linear_reset(model, power=2, use_f=True).pvalue
    }

    # Load the prompt template
    prompt_filepath = 'ai_regression_analysis.txt'
    prompt_file_path = os.path.join(
        os.path.dirname(__file__),
        'prompts',
        prompt_filepath
    )
    prompt_template = load_prompt(prompt_file_path)

    # Format the prompt with data
    prompt = prompt_template.format(
        r_squared=round(estimates['R_squared'], 3),
        adj_r_squared=round(estimates['Adj_R_squared'], 3),
        f_statistic=round(estimates['F_statistic'], 2),
        prob_f_statistic=round(estimates['Prob_F_statistic'], 2),
        t_statistic=round(estimates['t_statistic'], 3),
        p_value=round(estimates['P_value'], 3),
        omnibus=round(estimates['Omnibus'], 3),
        prob_omnibus=round(estimates['Prob(Omnibus)'], 3),
        jarque_bera=round(estimates['Jarque-Bera'], 3),
        prob_jb=round(estimates['Prob(JB)'], 3),
        skewness=round(estimates['Skewness'], 3),
        kurtosis=round(estimates['Kurtosis'], 3),
        breusch_pagan=round(estimates['Breusch_Pagan'], 3),
        prob_breusch_pagan=round(estimates['Breusch_Pagan'], 3),
        ramsey_reset=round(estimates['Ramsey_Reset'], 3),
        prob_ramsey_reset=round(estimates['Prob(RR)'], 3),
        durbin_watson=round(estimates['Durbin_Watson'], 3),
        condition_number=round(estimates['Condition_Number'], 2),
        intercept=round(estimates['Intercept'], 4),
        slope=round(estimates['Slope'], 4),
        slope_name=estimates['Slope_Name'],
        ai_model=ai_params.ai_model,
    )

    # Generate the AI analysis
    response = openai.chat.completions.create(
        model=ai_params.ai_model,
        messages=[
            {"role": "system",
             "content": "You are an expert data scientist. Your task is to "
                        "analyze the OLS regression results and provide a "
                        "detailed interpretation in markdown format for a "
                        "Jupyter notebook."
             },
            {"role": "user", "content": prompt}
        ],
        max_tokens=ai_params.max_tokens
    )

    # Remove the ```markdown``` delimiters from the response content
    analysis = response.choices[0].message.content.strip()
    if analysis.startswith("```markdown"):
        analysis = analysis[len("```markdown"):].strip()
    if analysis.endswith("```"):
        analysis = analysis[:-len("```")].strip()

    if ai_params.markdown:
        display(Markdown(analysis))
    else:
        return analysis
