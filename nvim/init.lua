-- some vim settings
vim.cmd("set expandtab")
vim.cmd("set tabstop=2")
vim.cmd("set softtabstop=2")
vim.cmd("set shiftwidth=2")

vim.cmd("set number")
vim.cmd("set numberwidth=4")

vim.g.mapleader = " "

-- load lazy.nvim
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable", -- latest stable release
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

local plugins = {
  { "catppuccin/nvim", name = "catppuccin", priority = 1000 },
  { "ellisonleao/glow.nvim", config = true, cmd = "Glow" }
}
local opts = { noremap = true, silent = true }

require("lazy").setup(plugins, opts)

-- color scheme
require("catppuccin").setup()
vim.cmd.colorscheme "catppuccin"

-- glow markdown
require("glow").setup({
  width_ratio = 0.9
})

-- Shorten function name
-- local keymap = vim.api.nvim_set_keymap

-- key mappings
vim.keymap.set("n", "+", "<C-a>") -- increment number
vim.keymap.set("n", "-", "<C-x>") -- decrement number

vim.keymap.set("n", "<x>", "_x") -- delete current char

vim.keymap.set("n", "<C-q>", ":q!") -- quit file
vim.keymap.set("n", "<C-w>", ":wq") -- write & quit file

vim.keymap.set("n", "<S-Up>", ":m-2<CR>") -- move line up
vim.keymap.set("n", "<S-Down>", ":m+<CR>") -- move line down
vim.keymap.set("n", "<S-d>", "yyp") -- duplicate line
vim.keymap.set("n", "<S-BS>", "<ESC>dd") -- delete line

vim.keymap.set("n", "<C-a>", "<ESC>cw") -- change rest of word
vim.keymap.set("n", "<C-s>", "<ESC>c)") -- change rest of sentence
vim.keymap.set("n", "<C-d>", "<ESC>C") -- change rest of line

vim.keymap.set("n", "<C-u>", "<ESC>mzgUiw") -- change complete word to uppercase
vim.keymap.set("n", "<C-l>", "<ESC>mzguiw") -- change complete word to lowercase

-- vim.keymap.set("n", "<C-y>", "<C-w>v") -- split view vertically

-- vim.keymap.set({"n", "i"}, "<Up>", "") -- disable arrow up
-- vim.keymap.set({"n", "i"}, "<Right>, "") -- disable arrow right
-- vim.keymap.set({"n", "i"}, "<Down>, "") -- disable arrow down
-- vim.keymap.set({"n", "i"}, "<Left>, "") -- disable arrow left

