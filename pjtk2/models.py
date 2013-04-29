from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse

from taggit.managers import TaggableManager

import datetime
import pdb

# Create your models here.


class ProjectsThisYear(models.Manager):
    def get_query_set(self):
        '''get all of the project objects from the current year'''
        use_for_related_fields = True
        yr = datetime.datetime.now().year
        return super(ProjectsThisYear, self).get_query_set().filter(
                     YEAR__gte=yr, Active=True)

class ProjectsLastYear(models.Manager):
    def get_query_set(self):
        '''get all of the project objects from last year'''
        use_for_related_fields = True
        yr = datetime.datetime.now().year - 1
        return super(ProjectsLastYear, self).get_query_set().filter(
                    YEAR = yr, Active=True)


class Milestone(models.Model):
    '''Look-up table of reporting milestone'''

    #(database, display)
    MILESTONE_CHOICES = {
        ('Core', 'core'),
        ('Suggested', 'suggested'),    
        ('Custom', 'custom'),
    }

    label = models.CharField(max_length=30, unique=True)
    category = models.CharField(max_length=30, choices=MILESTONE_CHOICES,
                                default='Custom')
    order = models.IntegerField(default=99)

    class Meta:
        verbose_name = "Reporting Milestones"
        verbose_name_plural = "Reporting Milestones"
        ordering = ['order']

    def __unicode__(self):
        return self.label


class TL_ProjType(models.Model):
    Project_Type = models.CharField(max_length=150)
    #project_type_slug = SlugField(blank=True, editable=False)
    
    class Meta:
        verbose_name = "Project Type"
    
    def __unicode__(self):
        return self.Project_Type

    #def save(self, *args, **kwargs):
    #    """
    #    from:http://stackoverflow.com/questions/7971689/
    #         generate-slug-field-in-existing-table
    #    Slugify name if it doesn't exist.
    #    """
    #    if not self.project_type_slug:
    #        self.project_type_slug = slugify(self.Project_Type)
    #    super(Project_Type, self).save( *args, **kwargs)


class TL_Database(models.Model):
    MasterDatabase = models.CharField(max_length=250)
    Path = models.CharField(max_length=250)

    class Meta:
        verbose_name = "Master Database"
    
    def __unicode__(self):
        return self.MasterDatabase

class Project(models.Model):
    '''Class to hold a record for each project
     TODO:
     Add Lake, Active,
     factor out milestone to seperate table(s)
    '''

    #(database, display)
    FUNDING_CHOICES = {
        ('spa', 'SPA'),
        ('coa', 'COA'),    
        ('other', 'other'),
    }

    LAKE_CHOICES = {
        ('LH', 'Lake Huron'),
        ('LS', 'Lake Superior'),    
    }

    YEAR = models.CharField("Year", max_length=4, blank=True, editable=False)
    PRJ_DATE0 = models.DateField("Start Date", blank=False)
    PRJ_DATE1 = models.DateField("End Date", blank=False)
    PRJ_CD = models.CharField("Project Code", max_length=12, unique=True, blank=False)
    PRJ_NM = models.CharField("Proejct Name", max_length=50, blank=False)
    PRJ_LDR = models.CharField("Project Lead", max_length=40, blank=False)
    COMMENT = models.TextField(blank=False)
    MasterDatabase = models.ForeignKey("TL_Database")
    ProjectType = models.ForeignKey("TL_ProjType")

    Approved = models.BooleanField(default = False)
    Conducted  = models.BooleanField(default = False)
    FieldWorkComplete  = models.BooleanField(default = False)
    AgeStructures = models.BooleanField(default = False)
    DataScrubbed  = models.BooleanField(default = False)
    DataMerged  = models.BooleanField(default = False)
    SignOff  = models.BooleanField(default = False)
    
    Max_DD_LAT = models.DecimalField(max_digits=5, decimal_places=3, 
                                     null=True, blank=True)
    Min_DD_LAT = models.DecimalField(max_digits=5, decimal_places=3, 
                                     null=True, blank=True)
    Max_DD_LON = models.DecimalField(max_digits=5, decimal_places=3, 
                                     null=True, blank=True)
    Min_DD_LON = models.DecimalField(max_digits=5, decimal_places=3, 
                                     null=True, blank=True)
    Owner = models.ForeignKey(User, blank=True)

    Active  = models.BooleanField(default = True)
    Funding = models.CharField("Funding Source", max_length=30, choices=FUNDING_CHOICES,
                                default="spa")
    Lake =  models.CharField(max_length=30, choices=LAKE_CHOICES,
                                default="LH")

    TotalCost =  models.DecimalField("Total Cost", max_digits=8, decimal_places=2, 
                                     null=True, blank=True)

    slug = models.SlugField(blank=True, editable=False)
    tags = TaggableManager()

    #managers
    objects = models.Manager()
    last_year = ProjectsLastYear()
    this_year = ProjectsThisYear()


    class Meta:
        verbose_name = "Project List"
        ordering = ['-PRJ_DATE1']
        
    def ProjectSuffix(self):
        return self.PRJ_CD[-3:]

    def __unicode__(self):
        ret = "%s (%s)" % (self.PRJ_NM, self.PRJ_CD)
        return ret

    def get_assignments(self):
        '''get all of the reports have been assigned to 
        this project - no distinction between core or custom reports'''
        return ProjectReports.objects.filter(project=self)

    def get_core_assignments(self, all=True):
        '''get all of the core reports have been assigned to this
        project, if all is true, all assignements are returned, if all
        is False, only required assignments are returned.'''

        if all==True:
            assignments = self.get_assignments().filter(
                report_type__category='Core')
        else:
            assignments = self.get_assignments().filter(
                report_type__category='Core').filter(required=True) 
        return assignments

    def get_custom_assignments(self):
        '''get a list of any custom reports that have been assigned to
        this project'''
        return self.get_assignments().filter(required=True).exclude(
            report_type__category='Core')

    def get_complete(self):
        '''get the project reports that have uploaded reports
        associated with them.'''
        return ProjectReports.objects.filter(project=self).filter(
            report__in=Report.objects.filter(current=True,
                                             projectreport__project=self))

    def get_outstanding(self):
        '''these are the required reports that have not been submitted yet'''
        return ProjectReports.objects.filter(project=self).exclude(
            report__in=Report.objects.filter(projectreport__project=self))

    def get_reports(self):
        '''get all of the CURRENT reports that are associated with
        this project.  Non-current reports are not included in this recordset.'''
        return Report.objects.filter(current=True, 
                                     projectreport__project=self)


    def get_assignment_dicts(self):
        '''return a dictionary of dictionaries containing elements of
        all core and custom reports as well as vectors indicating
        which ones have been assigned to this project.'''

        #get a queryset of all reports we consider 'core'
        corereports = Milestone.objects.filter(category='Core')
        customreports = Milestone.objects.filter(category='Custom')
    
        #we need to convert the querset to a tuple of tuples
        corereports = tuple([(x[0], x[1]) for x in corereports.values_list()])
        customreports = tuple([(x[0], x[1]) for x in customreports.values_list()])    
        #see if there is a project associated with this slug, if so, get
        #the reports currently assigned to the project, if not return a
        #dictionary with all reports assigned
        core_assigned = self.get_core_assignments()
        core_assigned = [x.report_type_id for x in list(core_assigned)]

        custom_assigned = self.get_custom_assignments()
        custom_assigned = [x.report_type_id for x in list(custom_assigned)]
 
        #put the reports and assigned reports in a dictionary    
        Core = dict(reports=corereports, assigned=core_assigned)
        Custom = dict(reports=customreports, assigned=custom_assigned)

        reports = dict(Core=Core, Custom=Custom)
    
        return reports


    def resetMilestones(self):
        '''a function to make sure that all of the project milestones are
        set to zero. Used when copying an existing project - we don t want
        to copy its milestones too'''
        self.Approved = False
        self.Conducted = False
        self.DataScrubbed = False
        self.DataMerged = False                        
        self.SignOff = False
        return self

    def initialReports(self):
        '''A function that will add a record into "ProjectReports" for
        each of the core report for newly created projects'''
        #project = Project.objects.get(slug=slug)
        corereports = Milestone.objects.filter(category='Core')

        for report in corereports:
            pr = ProjectReports(project=self, report_type = report)
            pr.save()

    def get_family(self):   
       try:
           family = Family.objects.get(projectsisters__project=self)
       except:
           family = None
 
       return family

    def add_sister(self, slug):
        family = self.get_family()
        if family is None:
            family = Family.objects.create()
            ProjectSisters.objects.create(project=self, family=family)

        #now add the project associated with slug to family:
        project = Project.objects.get(slug=slug)
        ProjectSisters.objects.create(project=project, family=family)

    def get_sisters(self, excludeself = True):
        '''return a queryset of sister projects associated with this
        project. - By default, the current project is not incuded in
        the recordset'''
        family = self.get_family()
        if family:
            try:
                if excludeself:
                    sisters = Project.objects.filter(
                        projectsisters__family=family).exclude(slug=self.slug)
                else:
                    sisters = Project.objects.filter(
                        projectsisters__family=family)
            except:
                sisters = []
        else:
            sisters = []
        return sisters


    def get_sister_candidates(self):
        '''return a querset of projects that could be sisters to this
        project.  To be a candidates for sisterhood, a project must be
        approved, be the same project type, run in the same year and
        not be a sister to another project. If the current project
        isn't approved, no candidates will be returned regardless.'''
        if self.Approved:
            try:
                candidates = Project.objects.filter(Approved=True, 
                                            ProjectType=self.ProjectType, 
                                            YEAR = self.YEAR,
                                            projectsisters__isnull=True).exclude(
                                            slug=self.slug)
            except:
                candidates = []
        else:
            candidates = []
        return candidates
            

    def delete_sister(self, slug):
        project = Project.objects.get(slug=slug)
        ProjectSisters.objects.filter(project=project).delete()
        family = self.get_family()
        #if this was the last sibling in the family get rid of its
        #record and the family record too.
        familysize = ProjectSisters.objects.filter(family=family).count()
        if familysize==1:
            ProjectSisters.objects.filter(family=family).delete()
            Family.objects.filter(id=family.id).delete()                    


    def disown(self):
        '''the special case when we want to remove this project from an
        existing family, but keep the other sister relationships intact.'''

        family = self.get_family()

        self.delete_sister(self.slug)
        #if this was the last sibling in the family get rid of it too.
        familysize = ProjectSisters.objects.filter(family=family.id).count()
        if familysize==1:
            ProjectSisters.objects.filter(family=family).delete()
            Family.objects.filter(id=family.id).delete()                    


    #@models.permalink
    def get_absolute_url(self):
        url = reverse('pjtk2.views.ProjectDetail', kwargs={'slug':self.slug})
        return url

    def save(self, *args, **kwargs):
        """
        from:http://stackoverflow.com/questions/7971689/
             generate-slug-field-in-existing-table
        Slugify name if it doesn't exist. IMPORTANT: doesn't check to see
        if slug is a dupicate!
        """
        new=False
        if not self.slug or not self.YEAR:
            self.slug = slugify(self.PRJ_CD)
            self.YEAR = self.PRJ_DATE0.year
            new = True

        super(Project, self).save( *args, **kwargs)
        if new:
            self.initialReports()
    
            
class ProjectReports(models.Model):
    '''list of reporting requirements for each project'''
    project = models.ForeignKey('Project')
    report_type = models.ForeignKey('Milestone')
    required  = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ("project", "report_type",)
        verbose_name_plural = "Project Reports"
        
    def __unicode__(self):
        return "%s - %s" % (self.project.PRJ_CD, self.report_type)

        
class Report(models.Model):
    '''class for reports.  A single report can be linked to multiple
    entries in Project Reports'''
    current = models.BooleanField(default=True)
    projectreport = models.ManyToManyField('ProjectReports')
    #projectreport = models.ForeignKey('ProjectReports')
    #report_path = models.CharField(max_length = 300, default="")
    report_path = models.FileField(upload_to="reports/")
    uploaded_on = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length = 300)
    report_hash = models.CharField(max_length = 300)

    def __unicode__(self):
        return str(self.report_path)


class Bookmark(models.Model):
    '''a class to allow users to bookmark and unbookmark their
    favourite projects.'''
    project = models.ForeignKey(Project)
    user = models.ForeignKey(User, related_name = "project_bookmark")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __unicode__(self):
        return "%s" % self.project

    def get_project_url(self):
        return self.project.get_absolute_url()

    def name(self):
        return self.project.PRJ_NM
        
    def get_project_code(self):
        return self.project.PRJ_CD

    def ProjectType(self):
        return self.project.ProjectType

    def YEAR(self):
        return self.project.YEAR

class Family(models.Model):
    '''Provides a mechanism to ensure that families are unique and
    auto-created.  The relationship between projects and families is
    essentailly an m2m, but currently djgano does not provide a
    mechanism to ensure that each project is associated with just one
    family.'''
    id = models.AutoField(primary_key=True)

    class Meta:
        verbose_name_plural = "Families"

    def __unicode__(self):
        return str("Family %s" % self.id)
        
    
class ProjectSisters(models.Model): 

    '''Sister projects have common presentations and summary reports.
    They must be the same project type, and run in the same year.'''  

    project = models.ForeignKey('Project') 
    family = models.ForeignKey('Family') 

    class Meta:
        verbose_name_plural = "Project Sisters"
        ordering = ['family', 'project']

    def __unicode__(self):
        return str("Project - %s - Family %s" % (self.project, self.family))


        
        
class AdminMilestone(admin.ModelAdmin):
    list_display = ('label', 'category',)


class AdminTL_ProjType(admin.ModelAdmin):
    pass

class AdminTL_Database(admin.ModelAdmin):
    pass

class AdminProject(admin.ModelAdmin):
    pass

class AdminFamily(admin.ModelAdmin):
    pass

class AdminProjectSisters(admin.ModelAdmin):
    pass

class AdminProjectReports(admin.ModelAdmin):
    list_display = ('project', 'report_type',)
    list_filter = ('project', 'report_type')

class AdminReport(admin.ModelAdmin):
    #list_display = ('current', 'ProjectReports_project', 'ProjectReports_report__type',)
    list_display = ('current', 'report_path','uploaded_on', 'uploaded_by')
    #    list_filter = ('ProjectReports__project',)



admin.site.register(Milestone, AdminMilestone)
admin.site.register(TL_ProjType, AdminTL_ProjType)
admin.site.register(TL_Database, AdminTL_Database)
admin.site.register(Project, AdminProject)
admin.site.register(ProjectReports, AdminProjectReports)
admin.site.register(Report, AdminReport)
admin.site.register(Family, AdminFamily)
admin.site.register(ProjectSisters, AdminProjectSisters)


