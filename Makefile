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

.PHONY: all
all:
	@echo "Try 'make help'"

.PHONY: help
help: ## 명령어 모음
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

.PHONY: setlocal
setlocal: ## local에서 settings.py 설정
	#$(LN) $(CONF)/$(SETDIR)/$(LOCFILE) $(CONF)/$(SETDIR)/$(SETFILE)
	$(LN) $(LOCFILE) $(CONF)/$(SETDIR)/$(SETFILE)
	# $(EXP) $(DJSET)=$(CONF).$(LOC)
	#$(EXP) $(DJSET)=$(CONF).$(SETDIR).$(LOC)

.PHONY: setprod
setprod: ## prod에서 settings.py 설정
	# $(LN) $(CONF)/$(SETDIR)/$(PRODFILE) $(CONF)/$(SETDIR)/$(SETFILE)
	$(LN) $(PRODFILE) $(CONF)/$(SETDIR)/$(SETFILE)
	# $(EXP) $(DJSET)=$(CONF).$(PROD)
	#$(EXP) $(DJSET)=$(CONF).$(SETDIR).$(PROD)

.PHONY: runserver
runserver: ## python manage.py runserver
	$(PY) $(MNG) runserver

.PHONY: migrations
migrations: ## python manage.py makemigrations
	$(PY) $(MNG) makemigrations $(a)

.PHONY: makemigrations
makemigrations: ## python manage.py makemigrations
	$(PY) $(MNG) makemigrations $(a)

.PHONY: migrate
migrate: ## python manage.py migrate
	$(PY) $(MNG) migrate $(a)

.PHONY: showmigrations
showmigrations: ## python manage.py showmigrations
	$(PY) $(MNG) showmigrations $(a)

.PHONY: sqlmigrate
sqlmigrate: ## python manage.py sqlmigrate 앱이름 migrations파일번호
	$(PY) $(MNG) sqlmigrate $(a) $(n)

.PHONY: shell
shell: ## python manage.py shell_plus --print-sql --quiet-load
	$(PY) $(MNG) shell_plus --print-sql --quiet-load

.PHONY: collectstatic
collectstatic: ## python manage.py collectstatic
	$(PY) $(MNG) collectstatic

.PHONY: app
app: ## python manage.py startapp 앱이름 ./apps/앱이름
	$(MKDIR) $(APPDIR)/$(a)
	$(PY) $(MNG) startapp $(a) ./$(APPDIR)/$(a)
	@echo "apps.py 가서 name에 apps 붙이기"

.PHONY: superuser
superuser: ## createsuperuser
	$(PY) $(MNG) shell < tools/create_superuser.py

.PHONY: test
test: ## python manage.py test
	$(PY) $(MNG) test

.PHONY: bim
bim: $(SCRIPT) ## black, isort, mypy, coverage
	$(SCRIPT)

.PHONY: install
install: ## poetry install
	$(PTR) install	

.PHONY: runstart
runstart: makemigrations migrate runserver ## makemigrations + migrate + runserver

.PHONY: start
start: ## docker db start
	$(DCK) start $(DBCONT)

.PHONY: stop
stop: ## docker db stop
	$(DCK) stop $(DBCONT)

.PHONY: exec
exec: ## enter the container
	$(DCK) exec -it $(DBCONT) /bin/sh

