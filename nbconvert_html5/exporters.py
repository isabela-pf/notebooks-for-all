import os
import os.path
from pathlib import Path
from traitlets import default, List, Callable, CUnicode, Instance, TraitType
from traitlets.config import Config
from nbconvert.exporters.html import HTMLExporter
from nbconvert.preprocessors import CSSHTMLHeaderPreprocessor
from bs4 import BeautifulSoup, Tag
from .selectors import MAIN, CODE, MD, OUT, PROMPT
from re import compile

DIR = Path(__file__).parent
PROMPT_RE = compile("(In|Out)(\s|&nbsp;){0,1}\[(?P<n>[0-9]+)\]")


def soupify(body):
    return BeautifulSoup(body, features="html.parser")


class PostProcessExporter(HTMLExporter):
    """an embellished HTMLExporter that allows modifications of exporting and the exported.

    the `nbconvert` exporter has a lot machinery for converting notebook data into strings.
    this class introduces a `post_process` trait that allows modifications after creating html content.
    this method allows tools like `html.parser` and `bs4.BeautifulSoup` to make modifications at the end.

    changes to the template and exporter machinery are foundational changes that take time.
    post modifications make it possible to quick changes in manual testing scenarios or configure
    def post_process_code_cell(self, cell):
        pass
    A/B testing with out requiring `nbconvert` or notebook knowleldge."""

    export_from_notebook = "html5"
    extra_template_paths = List([(DIR / "templates").absolute().__str__()])
    post_processor = Callable(lambda x: x).tag(config=True)

    def code_set_cell_label(self, cell, label=None):
        pass

    def post_process_cell(self, cell):
        pass

    def post_process_markdown_cell(self, cell):
        pass

    def post_process_code_cell(self, cell):
        pass

    # def _template_file_default(self):
    #     return "html5-lab.j2"


from traitlets import Bool, CUnicode


class Html5(PostProcessExporter):
    def from_notebook_node(self, nb, **kw):
        result, meta = super().from_notebook_node(nb, **kw)
        result = self.post_process_html(result)
        return str(result), meta

    notebook_is_main = Bool(True, help="transform notebook div to main").tag(config=True)
    notebook_code_cell_is_article = Bool(True, help="transform code cell div to article").tag(
        config=True
    )
    notebook_md_cell_is_article = Bool(True, help="transform mardown cell div to article").tag(
        config=True
    )
    cell_output_is_section = Bool(True, help="transform output div to section").tag(config=True)
    tab_to_code_cell = Bool(False, help="add tabindex to code cells for navigation").tag(
        config=True
    )
    tab_to_md_cell = Bool(False, help="add tabindex to md cells for navigation").tag(config=True)
    tab_to_code_cell_display = Bool(False, help="add tabindex to cell displays for navigation").tag(
        config=True
    )
    code_cell_label = Bool(False, help="add aria-label to code cells").tag(config=True)
    md_cell_label = Bool(False, help="add aria-label to md cell").tag(config=True)
    cell_display_label = Bool(False, help="add aria-label to cell").tag(config=True)
    # contenteditable cells make a tag interactive.
    cell_contenteditable = Bool(False, help="make cell code inputs contenteditable").tag(
        config=True
    )
    cell_contenteditable_label = Bool(False, help="aria-label on contenteditable cells").tag(
        config=True
    )
    prompt_is_label = Bool(False, help="add the cell input number to the aria label").tag(
        config=True
    )

    cell_describedby_heading = Bool(
        False, help="set aria-describedby when heading found in markdown cell"
    ).tag(config=True)

    increase_prompt_visibility = Bool(
        True, help="decrease prompt transparency for better color contrast"
    ).tag(config=True)

    cell_focus_style = CUnicode(
        """outline: 1px dashed;""",
        help="the focus style to apply to tabble cells.",
        allow_none=True,
    ).tag(config=True)

    include_toc = Bool(
        False, help="include a top of contents in the page"  # this will likely need styling.
    )
    # add toc as as a markdown cell? can't cause there is no canonical plage for it.
    # the natural place for a table of contents is based on the dom structure.
    # if the headings are links then they can be tabbed to.
    h_is_link = Bool(False, help="markdown headings h1..6 are links that get tabbed to.").tag(
        config=True
    )
    scroll_to_top = Bool(False, help="include a scroll to top link").tag(config=True)

    def post_process_head(self, soup):
        script = soup.new_tag("style", type="text/css", rel="stylesheet")
        script.string = ""
        if self.increase_prompt_visibility:
            script.string += """
:root {
    --jp-cell-prompt-not-active-opacity: 1;
}
"""
        if self.cell_focus_style:
            script.string += (
                """.jp-Cell:focus {
    %s
} 
"""
                % self.cell_focus_style
            )
        soup.select_one("head").append(script)

    def post_process_html(self, body):
        soup = soupify(body)
        if self.notebook_is_main:
            soup.select_one(MAIN).name = "main"

        soup.select_one("html").attrs["lang"] = "en"

        self.post_process_head(soup)

        self.post_process_cells(soup)
        if self.scroll_to_top:
            footer = soup.select_one("main footer")
            if not footer:
                footer = Tag(name="footer")
                soup.select_one("main").append(footer)
            a = Tag(name="a", attrs=dict(href="#top"))
            a.string = "Scroll to top"
            b = Tag(name="span", attrs=dict(id="top"))
            footer.append(a)
            soup.select_one("main").insert(0, b)
        return str(soup)

    def post_process_cells(self, soup):
        for element in soup.select(CODE):
            self.post_process_code_cell(element)

        for element in soup.select(MD):
            self.post_process_markdown_cell(element)

    def post_process_code_cell(self, cell):
        if self.notebook_code_cell_is_article:
            cell.name = "article"

        if self.tab_to_code_cell:
            cell.attrs["tabindex"] = 0  # when we do this we need add styling

        if self.code_cell_label:
            # https://ericwbailey.website/published/aria-label-is-a-code-smell/
            cell.attrs["aria-label"] = "cell"
            if self.prompt_is_label:
                prompt = cell.select_one(PROMPT)
                m = PROMPT_RE.match(prompt.text)
                if m and self.prompt_is_label:
                    cell.attrs["aria-label"] += " {}".format(m.group("n"))

        if self.cell_contenteditable:
            input = cell.select_one("code")
            input.attrs["contenteditable"] = "false"
            if self.cell_contenteditable_label:
                input.attrs["aria-label"] += " input {}".format(m.group("n"))

        if self.tab_to_code_cell:
            cell.attrs["tabindex"] = 0  # when we do this we need add styling

        self.post_process_displays(cell)

    def post_process_displays(self, cell):
        for out in cell.select(OUT):
            self.post_process_display(out)

    def post_process_display(self, display):
        if self.cell_output_is_section:
            display.name = "section"

        if self.cell_display_label:
            display.attrs["aria-label"] = f"display"
            if self.prompt_is_label:
                prompt = display.select_one(PROMPT)
                if prompt:
                    m = PROMPT_RE.match(prompt.text)
                    if m:
                        display.attrs["aria-label"] += " output {}".format(m.group("n"))
        if self.tab_to_code_cell_display:
            display.attrs["tabindex"] = 0  # when we do this we need add styling

    def post_process_markdown_cell(self, cell):
        if self.notebook_md_cell_is_article:
            cell.name = "article"

        if self.md_cell_label:
            # https://ericwbailey.website/published/aria-label-is-a-code-smell/
            cell.attrs["aria-label"] = "markdown"

            if self.cell_describedby_heading:
                heading = cell.select_one("h1,h2,h3,h4,h5,h6")
                if heading:
                    if "id" in heading.attrs:
                        cell.attrs["aria-describedby"] = heading.attrs["id"]

        if self.tab_to_md_cell:
            cell.attrs["tabindex"] = 0  # when we do this we need add styling

        if self.h_is_link:
            for e in cell.select("h1,h2,h3,h4,h5,h6"):
                id = e.attrs.get("id")
                if id:
                    a = Tag(name="a")
                    a.attrs["href"] = f"#{id}"
                    a.extend(list(e.children))
                    e.clear()
                    e.append(a)
                    e.select_one(".anchor-link").decompose()

    @classmethod
    def generate_config(cls):
        s = """c.NbConvertApp.export_format = "html5"
c.CSSHTMLHeaderPreprocessor.style = "default"
"""
        for k, v in vars(cls).items():
            if isinstance(v, TraitType):
                val = v.default_value
                if isinstance(val, str):
                    val = f'''"{val}"'''
                s += f"c.{cls.__name__}.{k} = {val} # {v.help}\n"
        return s

    @classmethod
    def write_config(cls, dir=Path.cwd(), file="jupyter_nbconvert_config.py"):

        target = Path(dir, file)
        if target.exists():
            raise FileExistsError(target)

        print(f"writing config to {target}")
        target.write_text(cls.generate_config())
