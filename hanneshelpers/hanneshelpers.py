def initiate_global_vars():
  from easynmt import EasyNMT
  from transformers import pipeline
  import string
  translation_analysis = EasyNMT('opus-mt')
  sentiment_analysis = pipeline("sentiment-analysis",model="siebert/sentiment-roberta-large-english")
  punct_table = str.maketrans({key: None for key in string.punctuation})
  return(translation_analysis, sentiment_analysis, punct_table)

def translate_and_correct(translation_analysis, lang, outputcsv):
  from textblob import TextBlob
  outputcsv["text"] = outputcsv["text"].str.replace("\!\!+", "!") 
  outputcsv["text"] = outputcsv["text"].str.replace("\?\?+", "?") 
  print(lang == "German")
  if lang == "German":
    trans = translation_analysis.translate(outputcsv["text"], source_lang = "de", target_lang = "en")
  elif lang == "Spanish":
    trans = translation_analysis.translate(outputcsv["text"], source_lang = "es", target_lang = "en")
  elif lang == "French":
    trans = translation_analysis.translate(outputcsv["text"], source_lang = "fr", target_lang = "en")
  elif lang == "English":
    trans = []
    for t in outputcsv["text"]:
        textBlb = TextBlob(t)           
        trans.append(str(textBlb.correct()))
  else:
      raise Exception('language not implemented')
  trans = [trans[i] if outputcsv.text[i] != "-" else "-" for i in range(len(trans))]
  outputcsv["trans"] = trans
  return(outputcsv)

def get_aggregate_sentiment(sentiment_analysis, neutral_words, outputcsv, i, punct_table):
  import numpy as np
  if outputcsv.trans[i].lower().translate(punct_table) in neutral_words:
  	sentiment_cont = sentiment_cat = 0
  else:
  	try:
  		s = sentiment_analysis(outputcsv.trans[i])[0]
  		if s['label'] == "NEGATIVE":
  			sign = -1
  		else:
  			sign = 1
  		sentiment_cont = sign * s['score']
  		sentiment_cat = sign * (s['score'] > 0.95)
  	except:
  		sentiment_cont = sentiment_cat = 0
  		print("error at:" + outputcsv.trans[i])
  outputcsv.loc[i, "sentiment_continuous"] = np.round(sentiment_cont * 100)
  outputcsv.loc[i, "sentiment_categorical"] = sentiment_cat
  return(sentiment_cat, sentiment_cont, outputcsv)

def update_statistics(n, n_pos, n_neg, sentiment_cat, sentiment_cont):
  import numpy as np
  n += 1
  n_pos += (sentiment_cont > 0)		
  n_neg += (sentiment_cont < 0)
  prob_posit_user = (n_pos  / n) 
  prob_negat_user = (n_neg / n) 
  prob_max = np.max([prob_posit_user, prob_negat_user])
  error =  1.96 * np.sqrt((prob_max * (1-prob_max))/n)
  return(n, n_pos, n_neg, prob_posit_user, prob_negat_user, error)

def update_highlights(sentiment_cont, highscores, highscores_i, lowscores, lowscores_i, i, df):
  import numpy as np
  if (sentiment_cont > np.min(highscores)) and (df.loc[i, "text_low"] not in df.loc[highscores_i, "text_low"].values):
  	highscores_i = np.array([i, highscores_i[np.argmax(highscores)]])
  	highscores = np.array([sentiment_cont, np.max(highscores)])
  elif sentiment_cont < np.max(lowscores) and (df.loc[i, "text_low"] not in df.loc[lowscores_i, "text_low"]):
  	lowscores_i = np.array([i, lowscores_i[np.argmin(lowscores)]])
  	lowscores = np.array([sentiment_cont, np.min(lowscores)])
  return(highscores, highscores_i, lowscores, lowscores_i)

def plot_current_sentiment_totals(prob_posit_user, prob_negat_user, error):
  import matplotlib.pyplot as plt
  import numpy as np

  plt.close('all')
  pos_perc = 100*prob_posit_user
  neg_perc = 100*prob_negat_user
  err_perc = 100*error
  ytop_pos = np.min([99 - pos_perc, err_perc])
  ybot_pos = np.min([pos_perc - 1, err_perc])
  ytop_neg = np.min([99 - neg_perc, err_perc])
  ybot_neg = np.min([neg_perc - 1, err_perc])
  fig, ax = plt.subplots(1, 2)
  ax[0].bar("Positivity", pos_perc, align='center', alpha=0.5, ecolor='black', capsize=10, color = "#378ce9") #yerr=100*error,
  ax[1].bar("Negativity", neg_perc, align='center', alpha=0.5, ecolor='black', capsize=10, color = "#378ce9")
  ax[0].errorbar(x = ["Positivity"], y = [pos_perc], yerr = ([ybot_pos], [ytop_pos]))
  ax[1].errorbar(x = ["Negativity"], y = [neg_perc], yerr = ([ybot_neg], [ytop_neg]))
  ax[0].yaxis.grid(True)
  ax[1].yaxis.grid(True)
  plt.tight_layout()
  ax[0].set_ylim([0, 100])
  ax[1].set_ylim([0, 100])
  plt.show()

def display_highlights(df, highscores_i, lowscores_i, analysis_var):
  from IPython.display import Markdown, display
  df["Highlights"] = df[analysis_var]
  df = df.loc[np.append(highscores_i, lowscores_i), :]
  display(pd.DataFrame(df["Highlights"]))

def display_group_comparison(outputcsv, comparison_var, df):
  import numpy as np
  from scipy.stats import ttest_ind

  if comparison_var != "No variable selected":
  	outputcsv[comparison_var] = df[comparison_var]
  	vals = list(set(outputcsv[comparison_var]))
  	if len(vals) != 2:
  		stop("Comparison variable must have exactly two possible values!")
  	else:
  		group1_label = vals[0]
  		group2_label = vals[1]
  		group1_ind = outputcsv[comparison_var] == group1_label
  		group2_ind = outputcsv[comparison_var] == group2_label
  		group1_mean = np.mean(outputcsv.sentiment_continuous[group1_ind])
  		group2_mean = np.mean(outputcsv.sentiment_continuous[group2_ind])
  		group1_std = np.std(outputcsv.sentiment_continuous[group1_ind])
  		group2_std = np.std(outputcsv.sentiment_continuous[group2_ind])
  		sidedness = np.where(group1_mean > group2_mean, "more positive sentiments", "more negative sentiments")
  		d = abs((group1_mean - group2_mean) / np.sqrt((group1_std ** 2 + group2_std **2) / 2))
  		d = np.round(d, 3)
  		if d < 0.1:
  			effsize = "negligible"
  		elif d < 0.2:
  			effsize = "small"
  		elif d < 0.5:
  			effsize = "medium"
  		else:
  			effsize = "large"
  		stat, p = ttest_ind(outputcsv.sentiment_continuous[group1_ind], outputcsv.sentiment_continuous[group2_ind])
  		significance = np.where(p < 0.05, "significantly", "not significantly")
  		p = np.round(p, 3)
  		print("Group " + str(group1_label) + " expressed " + str(sidedness) + " than group " + str(group2_label) +
  				".  \nThe magnitude of this difference can be considered " + effsize + " (Cohen's D: " + str(d) + ").  \n" +
  				"The effect is " + str(significance) + " different from zero (p-value: " + str(p) + ").")
  return(outputcsv)

def go(inputs):
  import numpy as np 
  import pandas as pd
  import matplotlib.pyplot as plt
  import time
  from IPython.display import Markdown, display

  df = inputs[0]
  analysis_var = inputs[1].widget.children[0].value
  comparison_var = inputs[2].widget.children[0].value
  lang = inputs[3].widget.children[0].value

  neutral_words = ['','nothing','none',"i don't know","don't know",'more or less no','none appreciable','no idea',
  'no feelings','i feel nothing',"i don't think of anything",'it does not trigger any emotions','neutral',
  'no associations','no emotions','no emotion','no feeling','neither good nor bad','neither positive nor negative','neither nor',
  "i don't know this",'nan','actually none',"can't describe in words","can't describe"]

  plt.rcParams['figure.dpi'] = 200
  plt.rcParams['figure.figsize'] = [2.8, 1.4]

  #load materials
  translation_analysis, sentiment_analysis, punct_table = initiate_global_vars()

  if (analysis_var != "No variable selected"):
    start = time.time()
    n = 4 #Agresti–Coull correction
    n_pos = n_neg = 2
    highscores = lowscores = highscores_i = lowscores_i = np.array([0])
    #prog_text, emoji_pic, barpl, result_table = st.empty(), st.empty(), st.empty(), st.empty()
    df[analysis_var] =  df[analysis_var].astype("str")
    df["text_low"] = [text.lower() for text in df[analysis_var]]
    df["text_low"] =  df["text_low"].astype("str")
    outputcsv = df.iloc[:, [0,1]].copy()
    outputcsv["text"] = df[analysis_var]
    outputcsv["trans"] = str()
    outputcsv["sentiment_categorical"] = int()
    outputcsv["sentiment_continuous"] = float()
    #translation and correction
    outputcsv = translate_and_correct(translation_analysis, lang, outputcsv)
    for i, text in enumerate(outputcsv.trans):
      #sentiment prediction and storing
      sentiment_cat, sentiment_cont, outputcsv = get_aggregate_sentiment(sentiment_analysis, neutral_words, outputcsv, i, punct_table)
      if sentiment_cat != 0: #for efficiency and mutual informativeness
        #update highlights
        highscores, highscores_i, lowscores, lowscores_i = update_highlights(sentiment_cont, highscores, highscores_i, lowscores, lowscores_i, i, df)

        #update statistics
        n, n_pos, n_neg, prob_posit_user, prob_negat_user, error = update_statistics(n, n_pos, n_neg, sentiment_cat, sentiment_cont)

    #display results table
    display(Markdown("****RESULTS****"))
    display(pd.DataFrame({"Positive": [str(np.round(prob_posit_user*100, 1)) + "%"], "Negative": [str(np.round(prob_negat_user*100, 1)) + "%"], "CI width": [str(np.round(2*error*100, 1))  + ' points'] }).style.hide_index())

    #sentiment plot update
    plot_current_sentiment_totals(prob_posit_user, prob_negat_user, error)

    #display final highlights
    display(Markdown("****HIGHLIGHTS / TEXT SAMPLES****"))
    display_highlights(df, highscores_i, lowscores_i, analysis_var)

    #display group comparison
    display(Markdown("****GROUP COMPARISON****"))
    outputcsv = display_group_comparison(outputcsv, comparison_var, df)

    #raw score download
    outputcsv.drop("trans", axis=1, inplace=True)
    outputcsv.to_csv('sentiment_scores.csv') 
    files.download('sentiment_scores.csv')

def user_input():
  from ipywidgets import interact
  import ipywidgets as widgets
  from google.colab import files
  import pandas as pd
  import io
  def returner(x):
    return(x)
  def returner2(x):
    return(x)
  def returner3(x):
    return(x)
  print("")
  print("Please upload the raw csv file from the analyzer:")
  uploaded = files.upload()
  my_file = list(uploaded)[0]
  df = pd.read_csv(io.BytesIO(uploaded[my_file]), encoding= "latin_1", sep = ";")
  print("Please select the column containing the texts:")
  analysis_v = interact(returner, x = list(df.columns.insert(0, "No variable selected"))) #
  print("Optionally select a column with binary values to compare groups in their sentiment:")
  comparison_v = interact(returner2, x = list(df.columns.insert(0, "No variable selected"))) #
  print("Please select the language of the texts:")
  lang_v = interact(returner3, x = ["English","German","Spanish","French", "Other"]) #
  return([df, analysis_v, comparison_v, lang_v])
