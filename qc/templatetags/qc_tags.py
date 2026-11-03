from django import template
register=template.Library()
@register.filter
def readable(value):
    labels={'gate1':'Gate 1 review','gate2':'Gate 2 review','start':'Work-order review','verification':'Verification in progress','readiness':'Readiness review','triggers':'Trigger review','welding':'Controlled welding','development':'Development','pending':'Pending evidence','draft':'Draft · review needed','approved':'Prototype approved','accepted':'Prototype accepted','qualified':'Prototype qualified','closed':'Closed','open':'Open','rejected':'Rejected','invalid':'Invalid evidence','valid':'Valid evidence','pass':'Meets stated basis','fail':'Does not meet stated basis','normal':'Conforming route','owner':'Owner action','picogrid':'Picogrid delegation','organization':'Organizational authority','action_required':'Disposition actions required','resolved':'Review resolved','procedure':'Procedure','machine':'Equipment','operator':'Operator'}
    return labels.get(str(value),str(value).replace('_',' ').capitalize())
@register.filter
def tone(value):
    if value in ('approved','accepted','qualified','closed','resolved','pass','valid','normal'):return 'green'
    if value in ('rejected','fail','open','invalid','action_required'):return 'red'
    return 'amber'
