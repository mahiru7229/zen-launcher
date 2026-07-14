LAUNCH_CONTROL_STYLE = '''
QLabel#StageBadge {
    background: #344329;
    color: #bde98a;
    border: 2px solid #12140f;
    padding: 4px 8px;
    font-size: 8.5pt;
    font-weight: 900;
}

QLabel#StageBadge[state="busy"] {
    background: #4a3824;
    color: #f0c37d;
}

QLabel#StageBadge[state="success"] {
    background: #344329;
    color: #bde98a;
}

QLabel#StageBadge[state="error"] {
    background: #5b302f;
    color: #ffd6d1;
}
'''
