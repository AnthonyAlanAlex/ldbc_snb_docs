FROM makisyu/texlive-2019

RUN yum install -y pandoc
RUN pip3 install pyyaml Jinja2
