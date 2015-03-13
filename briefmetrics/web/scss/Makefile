all: scss

CSS_OUT = ../static/css/screen.css
SCSS_LIBS = ./lib/ 
#SCSS_LIBS = $(wildcard briefmetrics/web/scss/lib/*/)

$(CSS_OUT): **.scss $(SCSS_LIBS)
	sassc --style compressed $(addprefix -I ,$(SCSS_LIBS)) screen.scss $(CSS_OUT)

scss: $(CSS_OUT)
