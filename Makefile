PY = python
MNG = manage.py
MKDIR = mkdir
LN = ln -sf
EXP = export

DJSET = DJANGO_SETTINGS_MODULE

PTR = poetry
CONF = config
SETDIR = settings
SET = settings
SETFILE = $(SET).py
LOC = local
LOCFILE = $(LOC).py
PROD = prod
PRODFILE = $(PROD).py
APPDIR = apps

DCK = docker
DBCONT = psqldb

SCRIPT = ./scripts/test.sh
SETTING = --settings=$(CONF).$(SETDIR).$(SET)
LOCSET = --settings=$(CONF).$(SETDIR).$(LOC)
PRODSET = --settings=$(CONF).$(SETDIR).$(PROD)

all:
	@echo "Try 'make help'"

help: ## 명령어 모음
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

setlocal: ## local에서 settings.py 설정
	#$(LN) $(CONF)/$(SETDIR)/$(LOCFILE) $(CONF)/$(SETDIR)/$(SETFILE)
	$(LN) $(LOCFILE) $(CONF)/$(SETDIR)/$(SETFILE)
	# $(EXP) $(DJSET)=$(CONF).$(LOC)
	#$(EXP) $(DJSET)=$(CONF).$(SETDIR).$(LOC)

setprod: ## prod에서 settings.py 설정
	# $(LN) $(CONF)/$(SETDIR)/$(PRODFILE) $(CONF)/$(SETDIR)/$(SETFILE)
	$(LN) $(PRODFILE) $(CONF)/$(SETDIR)/$(SETFILE)
	# $(EXP) $(DJSET)=$(CONF).$(PROD)
	#$(EXP) $(DJSET)=$(CONF).$(SETDIR).$(PROD)

runserver: ## python manage.py runserver
	$(PY) $(MNG) runserver

migrations: ## python manage.py makemigrations
	$(PY) $(MNG) makemigrations $(a)

makemigrations: ## python manage.py makemigrations
	$(PY) $(MNG) makemigrations $(a)

migrate: ## python manage.py migrate
	$(PY) $(MNG) migrate $(a)

showmigrations: ## python manage.py showmigrations
	$(PY) $(MNG) showmigrations $(a)

sqlmigrate: ## python manage.py sqlmigrate 앱이름 migrations파일번호
	$(PY) $(MNG) sqlmigrate $(a) $(n)

shell: ## python manage.py shell_plus --print-sql --quiet-load
	$(PY) $(MNG) shell_plus --print-sql --quiet-load

collectstatic: ## python manage.py collectstatic
	$(PY) $(MNG) collectstatic

app: ## python manage.py startapp 앱이름 ./apps/앱이름
	$(MKDIR) $(APPDIR)/$(a)
	$(PY) $(MNG) startapp $(a) ./$(APPDIR)/$(a)
	@echo "apps.py 가서 name에 apps 붙이기"

test: ## python manage.py test
	$(PY) $(MNG) test

bim: $(SCRIPT) ## black, isort, mypy, coverage
	$(SCRIPT)

install: ## poetry install
	$(PTR) install	

runstart: makemigrations migrate runserver ## makemigrations + migrate + runserver

start: ## docker db start
	$(DCK) start $(DBCONT)

stop: ## docker db stop
	$(DCK) stop $(DBCONT)

exec: ## enter the container
	$(DCK) exec -it $(DBCONT) /bin/sh

.PHONY: all help setlocal setprod runserver migrations makemigrations migrate showmigrations sqlmigrate collectstatic app test bim install start
