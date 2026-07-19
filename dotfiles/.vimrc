" --- appearance ---
syntax on                        " syntax highlighting (now actually visible)
set cursorline                   " highlight the current line
set ruler                        " line/column in the corner - position info without a number gutter
set showcmd                      " show partial commands while typing
set laststatus=2                 " always show the status line
set scrolloff=3                  " keep 3 lines of context around the cursor

" --- indentation (2 spaces) ---
set tabstop=2                    " a tab renders as 2 spaces
set softtabstop=2                " 2 spaces per tab while editing
set shiftwidth=2                 " 2 spaces for >>, << and autoindent
set expandtab                    " tabs become spaces
set autoindent                   " keep the previous indent on a new line
filetype plugin indent on        " filetype-aware indentation

" --- search ---
set hlsearch                     " highlight all matches
set incsearch                    " jump to the match while typing
set ignorecase                   " case-insensitive ...
set smartcase                    " ... unless the pattern has an uppercase letter
set showmatch                    " briefly show the matching bracket

" --- usability ---
set backspace=indent,eol,start   " make backspace work everywhere
set wildmenu                     " nicer command-line completion
set encoding=utf-8               " utf-8 everywhere
set mouse=                       " no mouse capture -> terminal copy/paste stays normal
set clipboard=unnamed            " yank/delete also go to the system clipboard
