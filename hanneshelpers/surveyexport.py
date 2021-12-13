def user_input():
  inputs = [None, None]
  from ipywidgets import interact
  def returner(Survey):
    inputs[0] = Survey
  def returner1(include_images):
    inputs[1] = include_images
  #def returner2(include_filters):
  #  inputs[2] = include_filters
  interact(returner, Survey = "Paste big thing here...")
  interact(returner1, include_images = False) 
  #interact(returner2, include_filters= False) 
  return(inputs)

def go(inputs):
  import json
  import requests
  from docx import Document
  from docx.shared import Inches
  from io import BytesIO
  import time
  #import PySimpleGUI as sg
  import os.path
  from docx.shared import Pt
  from docx.oxml.ns import nsdecls
  from docx.oxml import parse_xml
  t = inputs[0]
  include_images = inputs[1]
  include_filters = False #inputs[2]

  # layout = [
  #         [sg.Text("WARNING: So far, this is a quick and dirty solution.\n"
  #                  "The following information is not yet included in the final survey:\n"
  #                  "- multi filters on answers (if an answer has multiple filters, NO filter is shown)\n"
  #                  "- filter in matrix statements are currently not shown\n"
  #                  "- information whether question is randomized\n"
  #                  "- probably some other stuff - please tell Tim if you notice something")],
  #         [sg.Text("Paste raw text and wait a bit until I digested your input.")],
  #         [sg.Multiline(size=(50, 10), key='text_input')],
  #         [sg.Checkbox('Include images (takes +1 second per image)', enable_events=True, key = "CHECKBOX-IMAGE-CHECK")],
  #         [sg.Checkbox('Include answer filters (double check in the end - it is still buggy)', enable_events=True, key = "CHECKBOX-ANSWERTFILTER-CHECK")],
  #         [sg.Text("Select target folder where file should be saved"), sg.In(size=(15, 1), enable_events=True, key="-FOLDER-"),sg.FolderBrowse(button_color="white on black")],
  #         [sg.Button("Do the magic", button_color="white on darkgreen", size=(45,5))]     
  #         ]

  # window = sg.Window("Export surveys", layout, keep_on_top=False)

  #while True:
  #dictionary of question types:
  dict_qtypes = {"mc":"Multiple Choice",
            "freetext":"Offene Frage",
            "info":"Infobox",
            "matrix":"Matrix",
            "likert": "Likert",
            "imagecloud": "Bildvergleich (Galerie)",
            "image": "Bildvergleich (mit Bezeichnung)",
            "numericslider": "Numerischer Slider / NPS",
            "ranking": "Ranking",
            "starslider": "Stars",
            "propertyslider": "Präferenz-Slider",
            "number": "Zahl (Freie Eingabe)",
            "heatmap": "Heatmap",
            "videoplay": "Audio/Video",
            "photocaptur": "Fotoaufnahme"}


  # event, values = window.read()
  # if event == "Exit" or event == sg.WIN_CLOSED:
  #     break

  # select target folder for exporting the word file
  # if event == "-FOLDER-":
  #     folder = values["-FOLDER-"]
  #     folder = folder.replace('/', '\\')

  #Read text-value
  # if event == "Do the magic":   
  #     event, value = window.read() #read inserted values -> read shrinc factor
  json_string = t.rstrip()
  survey_raw = json.loads(json_string)

  document = Document()
  style = document.styles['Normal']
  font = style.font
  font.name = 'Roboto'
  font.size = Pt(10)
  paragraph_format = style.paragraph_format

  #Add header
  document.add_paragraph(survey_raw['title'])
  document.add_paragraph()

  # add table 
  table = document.add_table(1, 3)
  table.style = 'TableGrid'

  # populate header row 
  heading_cells = table.rows[0].cells
  heading_cells[0].paragraphs[0].add_run('Frage').bold = True
  heading_cells[1].paragraphs[0].add_run('Fragebogen').bold = True
  heading_cells[2].paragraphs[0].add_run('Fragetyp').bold = True

  # contents
  info_no = 1
  question_no = 1

  for i in range(len(survey_raw['questions'])): #question number
      cells = table.add_row().cells

      #cell 1 -------------
      if survey_raw['questions'][i]['qtype'] == 'info' or survey_raw['questions'][i]['qtype'] == 'videoplay':
          cells[0].paragraphs[0].add_run("Info "+str(info_no)).bold = True
          info_no += 1

      if survey_raw['questions'][i]['qtype'] != 'info' and survey_raw['questions'][i]['qtype'] != 'videoplay':
          cells[0].paragraphs[0].add_run("F"+str(question_no)).bold = True
          question_no += 1



      #cell 2 -------------
      #question wording -------------
      cells[1].paragraphs[0].add_run(survey_raw['questions'][i]['text']).bold = True
      paragraph_format.space_before = Pt(2)
      paragraph_format.space_after = Pt(2)

      #Include instructions for participants
      if "help" in survey_raw['questions'][i]: #check whether instructions for participants exist
          cells[1].add_paragraph(str(survey_raw['questions'][i]['help']))

      #Include image
      if include_images:
          if "media" in survey_raw['questions'][i]: #check whether image URL exist
              image_url = str(survey_raw['questions'][i]['media'])
              response = requests.get(image_url)
              binary_img = BytesIO(response.content)
              paragraph = cells[1].paragraphs[0]
              run = paragraph.add_run()
              run.add_picture(binary_img, width=Inches(2))
              time.sleep(1)

      cells[1].add_paragraph()

      #Answers -------------            
      if survey_raw['questions'][i]['qtype'] == 'matrix':
          cells[1].add_paragraph("Antworten:").bold = True

      #Answer text and letter
      answer_letter = 65 #because chr(65) = 'A'
      
      #Check for randomization
      random_answer = False
      random_answer_text = " "
      for j in range(len(survey_raw['questions'][i]['answers'])):
          if "random" in survey_raw['questions'][i]['answers'][j]:
              if survey_raw['questions'][i]['answers'][j]["random"] == True:
                  random_answer = True
      
      #If randomized:
      if random_answer == True:
          for j in range(len(survey_raw['questions'][i]['answers'])): #answers
              if survey_raw['questions'][i]['answers'][j]["random"] == False:
                  random_answer_text = " (nicht randomisiert)"
          

              answer_filter_text = " "
              if include_filters:
              
                  #Filter IF
                  if survey_raw['questions'][i]['answers'][j]["filterRequirements"] != []:
                      for k in range(len(survey_raw['questions'][i]['answers'][j]["filterRequirements"])):
                          filter_id = str(survey_raw['questions'][i]['answers'][j]["filterRequirements"][k])
                          for l in range(len(survey_raw['questions'])):
                              for m in range(len(survey_raw['questions'][l]['answers'])):
                                  if filter_id in survey_raw['questions'][l]['answers'][m]["filterId"]:   
                                      infoxboxes_until_here = info_no - 1
                                      filter_question_no = 1 + l - infoxboxes_until_here
                                      filter_answer_letter = 65 + m
                                      answer_filter_text = str(" (IF F"+str(filter_question_no)+str(chr(filter_answer_letter))+")"+random_answer_text)
                              for n in range(len(survey_raw['questions'][l]['key'])):
                                  if filter_id in survey_raw['questions'][l]['key'][n]["filterId"]:   
                                      infoxboxes_until_here = info_no - 1
                                      filter_question_no = 1 + l - infoxboxes_until_here
                                      filter_answer_letter = 65 + n
                                      answer_filter_text = str(" (IF F"+str(filter_question_no)+str(chr(filter_answer_letter))+")"+random_answer_text)

                  #Filter IF NOT
                  if survey_raw['questions'][i]['answers'][j]["filterNotRequirements"] != []:
                      for k in range(len(survey_raw['questions'][i]['answers'][j]["filterNotRequirements"])):
                          filter_id = str(survey_raw['questions'][i]['answers'][j]["filterNotRequirements"][k])
                          for l in range(len(survey_raw['questions'])):
                              for m in range(len(survey_raw['questions'][l]['answers'])):
                                  if filter_id in survey_raw['questions'][l]['answers'][m]["filterId"]:   
                                      infoxboxes_until_here = info_no - 1
                                      filter_question_no = 1 + l - infoxboxes_until_here
                                      filter_answer_letter = 65 + m
                                      answer_filter_text = str(" (IF NOT F"+str(filter_question_no)+str(chr(filter_answer_letter))+")"+random_answer_text)    
                              for n in range(len(survey_raw['questions'][l]['key'])):
                                      if filter_id in survey_raw['questions'][l]['key'][n]["filterId"]:   
                                          infoxboxes_until_here = info_no - 1
                                          filter_question_no = 1 + l - infoxboxes_until_here
                                          filter_answer_letter = 65 + n
                                          answer_filter_text = str(" (IF NOT F"+str(filter_question_no)+str(chr(filter_answer_letter))+")"+random_answer_text)
                                          

              answer_text = str(chr(answer_letter)+": "+survey_raw['questions'][i]['answers'][j]['text'] + answer_filter_text+random_answer_text)
              cells[1].add_paragraph(answer_text)
              answer_letter += 1
        
      if random_answer == False:
          for j in range(len(survey_raw['questions'][i]['answers'])): #answers
              answer_filter_text = " "
              if include_filters:
              
                  #Filter IF
                  if survey_raw['questions'][i]['answers'][j]["filterRequirements"] != []:
                      for k in range(len(survey_raw['questions'][i]['answers'][j]["filterRequirements"])):
                          filter_id = str(survey_raw['questions'][i]['answers'][j]["filterRequirements"][k])
                          for l in range(len(survey_raw['questions'])):
                              for m in range(len(survey_raw['questions'][l]['answers'])):
                                  if filter_id in survey_raw['questions'][l]['answers'][m]["filterId"]:   
                                      if survey_raw['questions'][i]['qtype'] == 'info' or survey_raw['questions'][i]['qtype'] == 'videoplay':
                                          infoxboxes_until_here = info_no
                                      else:
                                          infoxboxes_until_here = info_no - 1
                                      filter_question_no = 1 + l - infoxboxes_until_here
                                      filter_answer_letter = 65 + m
                                      answer_filter_text = str(" (IF F"+str(filter_question_no)+str(chr(filter_answer_letter))+")")
                              for n in range(len(survey_raw['questions'][l]['key'])):
                                  if filter_id in survey_raw['questions'][l]['key'][n]["filterId"]:   
                                      if survey_raw['questions'][i]['qtype'] == 'info' or survey_raw['questions'][i]['qtype'] == 'videoplay':
                                          infoxboxes_until_here = info_no
                                      else:
                                          infoxboxes_until_here = info_no - 1
                                      filter_question_no = 1 + l - infoxboxes_until_here
                                      filter_answer_letter = 65 + n
                                      answer_filter_text = str(" (IF F"+str(filter_question_no)+str(chr(filter_answer_letter))+")")

                  #Filter IF NOT
                  if survey_raw['questions'][i]['answers'][j]["filterNotRequirements"] != []:
                      for k in range(len(survey_raw['questions'][i]['answers'][j]["filterNotRequirements"])):
                          filter_id = str(survey_raw['questions'][i]['answers'][j]["filterNotRequirements"][k])
                          for l in range(len(survey_raw['questions'])):
                              for m in range(len(survey_raw['questions'][l]['answers'])):
                                  if filter_id in survey_raw['questions'][l]['answers'][m]["filterId"]:   
                                      infoxboxes_until_here = info_no - 1
                                      filter_question_no = 1 + l - infoxboxes_until_here
                                      filter_answer_letter = 65 + m
                                      answer_filter_text = str(" (IF NOT F"+str(filter_question_no)+str(chr(filter_answer_letter))+")")    
                              for n in range(len(survey_raw['questions'][l]['key'])):
                                      if filter_id in survey_raw['questions'][l]['key'][n]["filterId"]:   
                                          infoxboxes_until_here = info_no - 1
                                          filter_question_no = 1 + l - infoxboxes_until_here
                                          filter_answer_letter = 65 + n
                                          answer_filter_text = str(" (IF NOT F"+str(filter_question_no)+str(chr(filter_answer_letter))+")")
                                          

              answer_text = str(chr(answer_letter)+": "+survey_raw['questions'][i]['answers'][j]['text'] + answer_filter_text)
              cells[1].add_paragraph(answer_text)
              answer_letter += 1
      
      #Anweisung für Teilnehmer
      if "allowCustomText" in survey_raw['questions'][i]:
          if survey_raw['questions'][i]["allowCustomText"] == True:
              freetex_answer_test = survey_raw['questions'][i]["customTextName"]
              cells[1].add_paragraph(str(str(freetex_answer_test)+" (Freitext)"))
      
      #info texts        
      if survey_raw['questions'][i]['qtype'] == 'info' or survey_raw['questions'][i]['qtype'] == 'videoplay':
          try:
              cells[1].add_paragraph(str(survey_raw['questions'][i]['infoText']))
          except: None

      #include images
      for j in range(len(survey_raw['questions'][i]['answers'])):
          if include_images:
              if "imageUrl" in survey_raw['questions'][i]['answers'][j]: #check whether image URL exist
                  image_url = str(survey_raw['questions'][i]['answers'][j]['imageUrl'])
                  print(image_url)
                  response = requests.get(image_url)
                  binary_img = BytesIO(response.content)
                  paragraph = cells[1].paragraphs[0]
                  run = paragraph.add_run()
                  run.add_picture(binary_img, width=Inches(2))
                  time.sleep(1)
      
      #matrix scale items
      random_mat_items = False
      random_mat_items_text = " "
      for j in range(len(survey_raw['questions'][i]['rows'])):
          if "random" in survey_raw['questions'][i]['rows'][j]:
              if survey_raw['questions'][i]['rows'][j]["random"] == True:
                  random_mat_items = True
      
      #if randomized
      if random_mat_items == True:
          for j in range(len(survey_raw['questions'][i]['rows'])): #answers
              if survey_raw['questions'][i]['rows'][j]["random"] == False:
                  random_mat_items_text = " (nicht randomisiert)"
      
          answer_letter = 65 #because chr(65) = 'A'    
          if survey_raw['questions'][i]['rows'] != []: #Test whether matrix items exist
              cells[1].add_paragraph()
              cells[1].add_paragraph("Items:")
              for k in range(len(survey_raw['questions'][i]['rows'])): #matrix items
                  item_text = str(chr(answer_letter)+": "+survey_raw['questions'][i]['rows'][k]['text']+random_mat_items_text)
                  cells[1].add_paragraph(item_text)
                  answer_letter += 1
      
      #if not randomized
      if random_mat_items == False:
      
          answer_letter = 65 #because chr(65) = 'A'    
          if survey_raw['questions'][i]['rows'] != []: #Test whether matrix items exist
              cells[1].add_paragraph()
              cells[1].add_paragraph("Items:")
              for k in range(len(survey_raw['questions'][i]['rows'])): #matrix items
                  item_text = str(chr(answer_letter)+": "+survey_raw['questions'][i]['rows'][k]['text'])
                  cells[1].add_paragraph(item_text)
                  answer_letter += 1
      
      #likert scale
      answer_letter = 65 #because chr(65) = 'A'    
      if survey_raw['questions'][i]['key'] != []: #Test whether matrix items exist
          for k in range(len(survey_raw['questions'][i]['key'])): #matrix items
              item_text = str(chr(answer_letter)+": "+survey_raw['questions'][i]['key'][k]['text'])
              cells[1].add_paragraph(item_text)
              answer_letter += 1


      #cell 3 -------------
      #"Fragetyp" -------------

      if survey_raw['questions'][i]['qtype'] != "mc":
          for abbreviation, new_label in dict_qtypes.items():
              if abbreviation == survey_raw['questions'][i]['qtype']:
                  question_type = survey_raw['questions'][i]['qtype'].replace(abbreviation, new_label)
          cells[2].paragraphs[0].add_run(question_type) 

      #if survey_raw['questions'][i]['qtype'] == "mc":
      else:
          if 'multioptions' in survey_raw['questions'][i]:
              if survey_raw['questions'][i]['multioptions'] == False:
                  cells[2].paragraphs[0].add_run("Single Choice")
              else: 
                  cells[2].paragraphs[0].add_run("Multiple Choice")
                  
      #Randomisation
      if random_mat_items == True: 
          cells[2].add_paragraph("(Items randomisiert)")
      
      if random_answer == True:
          cells[2].add_paragraph("(Antworten randomisiert)")
          
      #Max options
      if "maxOptions" in survey_raw['questions'][i]:
          cells[2].add_paragraph("Max Antworten: "+str(survey_raw['questions'][i]['maxOptions']))
          
      #Min options
      if "minOptions" in survey_raw['questions'][i]:
          cells[2].add_paragraph("Min Antworten: "+str(survey_raw['questions'][i]['minOptions']))

      #Do filter exist?
      if survey_raw['questions'][i]["filterRequirements"] != [] or survey_raw['questions'][i]["filterNotRequirements"] != []:
          cells[2].add_paragraph()
          cells[2].add_paragraph("Filter:")

      #Filter IF
      if survey_raw['questions'][i]["filterRequirements"] != []:
          for k in range(len(survey_raw['questions'][i]["filterRequirements"])):
              filter_id = str(survey_raw['questions'][i]["filterRequirements"][k])
              for l in range(len(survey_raw['questions'])):
                  if survey_raw['questions'][l]['answers'] != []: 
                      for m in range(len(survey_raw['questions'][l]['answers'])):
                          if filter_id in survey_raw['questions'][l]['answers'][m]["filterId"]:
                              if survey_raw['questions'][l]['qtype'] == 'info' or survey_raw['questions'][l]['qtype'] == 'videoplay':
                                  infoxboxes_until_here = info_no
                              else:
                                  infoxboxes_until_here = info_no - 1
                              print("Infoboxes:" +str(infoxboxes_until_here))
                              print("l:"+str())
                              filter_question_no = 1 + l - infoxboxes_until_here
                              print("filter_qestion:" +str(filter_question_no))
                              filter_answer_letter = 65 + m
                              cells[2].add_paragraph("IF F"+str(filter_question_no)+str(chr(filter_answer_letter)))
                  elif survey_raw['questions'][l]['key'] != []:
                      for n in range(len(survey_raw['questions'][l]['key'])):
                          if filter_id in survey_raw['questions'][l]['key'][n]["filterId"]:
                              if survey_raw['questions'][l]['qtype'] == 'info' or survey_raw['questions'][l]['qtype'] == 'videoplay':
                                  infoxboxes_until_here = info_no
                              else:
                                  infoxboxes_until_here = info_no - 1
                              filter_question_no = 1 + l - infoxboxes_until_here
                              filter_answer_letter = 65 + n
                              cells[2].add_paragraph("IF F"+str(filter_question_no)+str(chr(filter_answer_letter)))
                          

      #Filter IF NOT
      elif survey_raw['questions'][i]["filterNotRequirements"] != []:
          for k in range(len(survey_raw['questions'][i]["filterNotRequirements"])):
              filter_id = str(survey_raw['questions'][i]["filterNotRequirements"][k])
              for l in range(len(survey_raw['questions'])):
                  if survey_raw['questions'][l]['answers'] != []:
                      for m in range(len(survey_raw['questions'][l]['answers'])):
                          if filter_id in survey_raw['questions'][l]['answers'][m]["filterId"]:   
                              infoxboxes_until_here = info_no - 1
                              filter_question_no = 1 + l - infoxboxes_until_here
                              filter_answer_letter = 65 + m
                              cells[2].add_paragraph("IF NOT F"+str(filter_question_no)+str(chr(filter_answer_letter)))
                  if survey_raw['questions'][l]['key'] != []:
                      for n in range(len(survey_raw['questions'][l]['key'])):
                          if filter_id in survey_raw['questions'][l]['key'][n]["filterId"]:   
                              infoxboxes_until_here = info_no - 1
                              filter_question_no = 1 + l - infoxboxes_until_here
                              filter_answer_letter = 65 + n
                              cells[2].add_paragraph("IF NOT F"+str(filter_question_no)+str(chr(filter_answer_letter)))

  #Layout stuff
  for row in table.rows:
      for cell, width in zip(row.cells, (Inches(0.72), Inches(5.1), Inches(1.50))):
          cell.width = width

  # Set a cell background (shading) color to RGB D9D9D9. 
  shading1 = parse_xml(r'<w:shd {} w:fill="053149"/>'.format(nsdecls('w')))
  table.cell(0, 0)._tc.get_or_add_tcPr().append(shading1)
  shading2 = parse_xml(r'<w:shd {} w:fill="053149"/>'.format(nsdecls('w')))
  table.cell(0, 1)._tc.get_or_add_tcPr().append(shading2)
  shading3 = parse_xml(r'<w:shd {} w:fill="053149"/>'.format(nsdecls('w')))
  table.cell(0, 2)._tc.get_or_add_tcPr().append(shading3)

  #Save it
  document.save(str(survey_raw['title']+'_export.docx'))