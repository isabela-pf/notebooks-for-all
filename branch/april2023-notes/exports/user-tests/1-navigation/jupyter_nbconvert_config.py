c.CSSHTMLHeaderPreprocessor.style = 'a11y-light'
c.Html5.notebook_is_main = True # transform notebook div to main
c.Html5.notebook_cell_is_article = True # transform cell div to article
c.Html5.cell_output_is_section = True # transform output div to section
c.Html5.tab_to_cell = True # add tabindex to cells for navigation
c.Html5.tab_to_cell_display = True # add tabindex to cell displays for navigation
c.Html5.cell_label = True # add aria-label to cell
c.Html5.cell_display_label = True # add aria-label to cell
c.Html5.prompt_is_label = True # add the cell input number to the aria label
c.Html5.cell_describedby_heading = True # set aria-describedby when heading found in markdown cell