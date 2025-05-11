## Cyclarity In-Vehicle SDK - Documentation Generation

# Requirements

apt requirements:
```
sudo apt install texlive-latex-recommended \
                texlive-fonts-recommended \
                texlive-fonts-extra tex-gyre \
                latexpdf
```

pip requirements:
```
pip install -r requirements.txt
```

# Generation
html format:
```
make html
```
PDF format:
```
make latexpdf LATEXMKOPTS="-silent"
```