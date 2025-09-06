function Div(el)
    if el.classes:includes("pagebreak") then
        if FORMAT:match("epub") or FORMAT:match("html") then
            return pandoc.RawBlock("html", '<div style="page-break-after: always;"></div>')
        elseif FORMAT:match("latex") then
            return pandoc.RawBlock("latex", "\\newpage")
        else
            return pandoc.Null()
        end
    end
    return nil
end
